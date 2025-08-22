# ===================================================================
# backend/main.py (最终完整版)
# ===================================================================

# --- 1. Imports ---
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from typing_extensions import Literal
import sqlalchemy
import paramiko # <--- 之前遗漏的、关键的 import

from database import database, servers, forwarding_rules
from models import (
    ServerCreate, ServerInfo, 
    RuleCreate, RuleInfo, 
    ServerStatus, ServerLogs
)
from security import encrypt_password, decrypt_password

# --- 2. FastAPI App Instance ---
app = FastAPI(title="Rathole Manager API")

# --- 3. CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. Database Connection Events ---
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# --- 5. API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to Rathole Manager API"}

# --- Server Management Endpoints ---

@app.post("/api/servers", response_model=ServerInfo, status_code=201)
async def add_server(server: ServerCreate):
    find_query = servers.select().where(
        (servers.c.hostname == server.hostname) | (servers.c.alias == server.alias)
    )
    existing_server = await database.fetch_one(find_query)
    if existing_server:
        detail = "Hostname" if existing_server.hostname == server.hostname else "Alias"
        raise HTTPException(status_code=400, detail=f"{detail} already exists")

    encrypted_pwd = encrypt_password(server.ssh_password)
    
    query = servers.insert().values(
        alias=server.alias,
        hostname=server.hostname,
        ssh_user=server.ssh_user,
        ssh_port=server.ssh_port,
        encrypted_password=encrypted_pwd,
        role=server.role
    )
    last_record_id = await database.execute(query)
    
    return ServerInfo(
        id=last_record_id,
        alias=server.alias,
        hostname=server.hostname,
        ssh_user=server.ssh_user,
        ssh_port=server.ssh_port,
        role=server.role
    )

@app.get("/api/servers", response_model=List[ServerInfo])
async def get_all_servers():
    query = servers.select()
    all_servers = await database.fetch_all(query)
    return [ServerInfo(**dict(s)) for s in all_servers]

@app.put("/api/servers/{server_id}", response_model=ServerInfo)
async def update_server(server_id: int, server_update: ServerCreate):
    find_query = servers.select().where(servers.c.id == server_id)
    existing_server = await database.fetch_one(find_query)
    if not existing_server:
        raise HTTPException(status_code=404, detail="Server not found")

    update_data = server_update.dict(exclude_unset=True)
    
    if server_update.ssh_password:
        update_data["encrypted_password"] = encrypt_password(server_update.ssh_password)
    if 'ssh_password' in update_data:
        del update_data["ssh_password"]
    
    if 'hostname' in update_data and update_data['hostname'] != existing_server.hostname:
        conflict_query = servers.select().where(servers.c.hostname == update_data['hostname'])
        if await database.fetch_one(conflict_query):
            raise HTTPException(status_code=400, detail="Hostname already exists")
    if 'alias' in update_data and update_data['alias'] != existing_server.alias:
        conflict_query = servers.select().where(servers.c.alias == update_data['alias'])
        if await database.fetch_one(conflict_query):
            raise HTTPException(status_code=400, detail="Alias already exists")

    update_query = servers.update().where(servers.c.id == server_id).values(**update_data)
    await database.execute(update_query)

    updated_server_query = servers.select().where(servers.c.id == server_id)
    return await database.fetch_one(updated_server_query)

@app.delete("/api/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(server_id: int):
    find_query = servers.select().where(servers.c.id == server_id)
    if not await database.fetch_one(find_query):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    delete_rules_query = forwarding_rules.delete().where(
        (forwarding_rules.c.client_id == server_id) | (forwarding_rules.c.server_id == server_id)
    )
    await database.execute(delete_rules_query)

    delete_server_query = servers.delete().where(servers.c.id == server_id)
    await database.execute(delete_server_query)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- Rule Management Endpoints ---

@app.post("/api/rules", response_model=RuleInfo, status_code=201)
async def add_forwarding_rule(rule: RuleCreate):
    client_query = servers.select().where(servers.c.id == rule.client_id)
    client = await database.fetch_one(client_query)
    if not client or client.role not in ['client', 'both']:
        raise HTTPException(status_code=404, detail=f"Invalid client_id: {rule.client_id}.")

    server_query = servers.select().where(servers.c.id == rule.server_id)
    server = await database.fetch_one(server_query)
    if not server or server.role not in ['server', 'both']:
        raise HTTPException(status_code=404, detail=f"Invalid server_id: {rule.server_id}.")

    port_conflict_query = forwarding_rules.select().where(
        (forwarding_rules.c.server_id == rule.server_id) & (forwarding_rules.c.remote_port == rule.remote_port)
    )
    if await database.fetch_one(port_conflict_query):
        raise HTTPException(status_code=400, detail=f"Remote port {rule.remote_port} is already in use.")

    query = forwarding_rules.insert().values(
        name=rule.name, rule_type=rule.rule_type, local_port=rule.local_port,
        remote_port=rule.remote_port, client_id=rule.client_id, server_id=rule.server_id
    )
    last_record_id = await database.execute(query)

    return RuleInfo(
        id=last_record_id, name=rule.name, rule_type=rule.rule_type,
        local_port=rule.local_port, remote_port=rule.remote_port, client_id=rule.client_id,
        server_id=rule.server_id, client_hostname=client.hostname, server_hostname=server.hostname,
        client_alias=client.alias, server_alias=server.alias
    )

@app.get("/api/rules", response_model=List[RuleInfo])
async def get_all_forwarding_rules():
    client_table = servers.alias("client")
    server_table = servers.alias("server")

    query = sqlalchemy.select(
        forwarding_rules,
        client_table.c.hostname.label("client_hostname"),
        server_table.c.hostname.label("server_hostname"),
        client_table.c.alias.label("client_alias"),
        server_table.c.alias.label("server_alias")
    ).select_from(
        forwarding_rules.join(client_table, forwarding_rules.c.client_id == client_table.c.id)
        .join(server_table, forwarding_rules.c.server_id == server_table.c.id)
    )
    results = await database.fetch_all(query)
    return [RuleInfo(**dict(r)) for r in results]

@app.put("/api/rules/{rule_id}", response_model=RuleInfo)
async def update_rule(rule_id: int, rule_update: RuleCreate):
    if not await database.fetch_one(forwarding_rules.select().where(forwarding_rules.c.id == rule_id)):
        raise HTTPException(status_code=404, detail="Rule not found")
    
    update_data = rule_update.dict()
    update_query = forwarding_rules.update().where(forwarding_rules.c.id == rule_id).values(**update_data)
    await database.execute(update_query)

    client_table = servers.alias("client")
    server_table = servers.alias("server")
    query = sqlalchemy.select(
        forwarding_rules,
        client_table.c.hostname.label("client_hostname"),
        server_table.c.hostname.label("server_hostname"),
        client_table.c.alias.label("client_alias"),
        server_table.c.alias.label("server_alias")
    ).select_from(
        forwarding_rules.join(client_table, forwarding_rules.c.client_id == client_table.c.id)
        .join(server_table, forwarding_rules.c.server_id == server_table.c.id)
    ).where(forwarding_rules.c.id == rule_id)
    
    return await database.fetch_one(query)

@app.delete("/api/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: int):
    if not await database.fetch_one(forwarding_rules.select().where(forwarding_rules.c.id == rule_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    
    delete_query = forwarding_rules.delete().where(forwarding_rules.c.id == rule_id)
    await database.execute(delete_query)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- Advanced Endpoints ---

@app.get("/api/servers/{server_id}/status", response_model=ServerStatus)
async def get_server_status(server_id: int):
    server = await database.fetch_one(servers.select().where(servers.c.id == server_id))
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    statuses = ServerStatus()
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=server.hostname, port=server.ssh_port,
            username=server.ssh_user, password=decrypt_password(server.encrypted_password),
            timeout=5
        )
        if server.role in ['server', 'both']:
            stdin, stdout, stderr = ssh.exec_command("systemctl is-active rathole-server.service")
            status = stdout.read().decode().strip()
            statuses.server_status = status if status else 'inactive'
        if server.role in ['client', 'both']:
            stdin, stdout, stderr = ssh.exec_command("systemctl is-active rathole-client.service")
            status = stdout.read().decode().strip()
            statuses.client_status = status if status else 'inactive'
        ssh.close()
    except Exception as e:
        print(f"Failed to check status for {server.hostname}: {e}")
        if server.role in ['server', 'both']: statuses.server_status = 'unknown'
        if server.role in ['client', 'both']: statuses.client_status = 'unknown'
    return statuses

@app.get("/api/servers/{server_id}/logs", response_model=ServerLogs)
async def get_server_logs(server_id: int, service_role: Literal['server', 'client']):
    server = await database.fetch_one(servers.select().where(servers.c.id == server_id))
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=server.hostname, port=server.ssh_port,
            username=server.ssh_user, password=decrypt_password(server.encrypted_password),
            timeout=10
        )
        service_name = f"rathole-{service_role}.service"
        command = f"journalctl -u {service_name} -n 50 --no-pager"
        stdin, stdout, stderr = ssh.exec_command(command)
        logs = stdout.read().decode().strip()
        if not logs:
            logs = stderr.read().decode().strip() or f"No logs found for {service_name}."
        ssh.close()
        return ServerLogs(logs=logs)
    except Exception as e:
        error_message = f"Failed to fetch logs for {server.hostname}: {e}"
        print(error_message)
        return ServerLogs(logs=error_message)

@app.post("/api/deploy", status_code=200)
async def trigger_deployment():
    try:
        from deployment_engine import run_deployment
        results = await run_deployment(database)
        return {"message": "Deployment process finished.", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    
@app.post("/api/servers/{server_id}/uninstall", status_code=200)
async def uninstall_server(server_id: int):
    """
    通过 SSH 连接到服务器并卸载 rathole 服务.
    """
    server = await database.fetch_one(servers.select().where(servers.c.id == server_id))
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # 定义要执行的清理命令列表
    uninstall_commands = [
        "systemctl stop rathole-server.service",
        "systemctl stop rathole-client.service",
        "systemctl disable rathole-server.service",
        "systemctl disable rathole-client.service",
        "rm -f /etc/systemd/system/rathole-server.service",
        "rm -f /etc/systemd/system/rathole-client.service",
        "systemctl daemon-reload",
        "rm -rf /etc/rathole",
        "rm -f /usr/local/bin/rathole" # 也删除二进制文件
    ]
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=server.hostname,
            port=server.ssh_port,
            username=server.ssh_user,
            password=decrypt_password(server.encrypted_password),
            timeout=10
        )

        all_errors = []
        print(f"🚀 Starting uninstall process on {server.hostname}...")
        for command in uninstall_commands:
            print(f"Executing: {command}")
            stdin, stdout, stderr = ssh.exec_command(command)
            # 等待命令执行完成，读取错误输出（如果有）
            error = stderr.read().decode().strip()
            if error:
                # 忽略 "Failed to stop service... not loaded" 这类无害的错误
                if "not loaded" not in error and "No such file or directory" not in error:
                    all_errors.append(f"CMD: `{command}`\nError: {error}")

        ssh.close()
        
        if all_errors:
            # 即使有错误，也认为卸载过程已尝试，返回成功但附带警告
            return {"message": "Uninstall process completed with some warnings.", "errors": all_errors}

        return {"message": f"Successfully uninstalled services from {server.hostname}."}

    except Exception as e:
        error_message = f"Failed to connect or execute uninstall on {server.hostname}: {e}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)

