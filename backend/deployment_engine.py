# backend/deployment_engine.py
import paramiko
import os
from jinja2 import Environment, FileSystemLoader
import secrets
from security import decrypt_password
from io import BytesIO
import traceback


# Rathole 最新版本下载地址 (amd64架构)
RATHOLE_DOWNLOAD_URL = "https://github.com/rapiz1/rathole/releases/download/v0.5.0/rathole-x86_64-unknown-linux-gnu.zip"

# 获取当前脚本 (deployment_engine.py) 所在的目录的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))
# 将脚本目录和 'templates' 文件夹名拼接成一个绝对路径
template_dir = os.path.join(script_dir, 'templates')
# 使用这个绝对路径来初始化 Jinja2 环境
env = Environment(loader=FileSystemLoader(template_dir))

def _generate_configs(servers, rules):
    """
    根据服务器和规则数据，生成所有配置文件内容。
    返回一个字典，key为server_id，value为一个包含配置信息的列表，
    例如: {1: [{'role': 'server', 'content': '...'}, {'role': 'client', 'content': '...'}]}
    """
    configs = {}
    token = secrets.token_hex(16)

    server_map = {s['id']: s for s in servers}
    
    for server in servers:
        server_id = server['id']
        configs[server_id] = []

        # 角色判断和配置生成
        # 1. 如果角色是 server 或 both, 生成 server 配置
        if server['role'] in ['server', 'both']:
            template = env.get_template('server.toml.j2')
            # 找到所有以当前服务器作为服务端的规则
            exposed_rules = [
                {**r, "token": token} for r in rules if r['server_id'] == server_id
            ]
            if exposed_rules:
                server_config_content = template.render(services=exposed_rules)
                configs[server_id].append({'role': 'server', 'content': server_config_content})

        # 2. 如果角色是 client 或 both, 生成 client 配置
        if server['role'] in ['client', 'both']:
            template = env.get_template('client.toml.j2')
            # 找到所有以当前服务器作为客户端的规则
            client_rules = [
                {**r, "token": token} for r in rules if r['client_id'] == server_id
            ]
            # 按服务端IP分组规则，因为一个客户端可能连接多个服务端
            remote_server_map = {}
            for rule in client_rules:
                if rule['server_id'] not in remote_server_map:
                    remote_server_map[rule['server_id']] = []
                remote_server_map[rule['server_id']].append(rule)
            
            # 为每一个服务端生成一个客户端配置
            # (简化：这里假设一个客户端只连一个服务端，因此只处理第一个)
            if remote_server_map:
                first_server_id = list(remote_server_map.keys())[0]
                rules_for_this_remote = remote_server_map[first_server_id]
                remote_server_hostname = server_map[first_server_id]['hostname']

                client_config_content = template.render(
                    services=rules_for_this_remote,
                    remote_server_addr=remote_server_hostname
                )
                configs[server_id].append({'role': 'client', 'content': client_config_content})

    return configs


def _deploy_to_host(server_info, configs_to_deploy):
    hostname = server_info['hostname']
    ssh_user = server_info['ssh_user']
    ssh_port = server_info['ssh_port']
    password = decrypt_password(server_info['encrypted_password'])

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"🚀 Connecting to {hostname}:{ssh_port}...")
        ssh.connect( hostname, port=ssh_port, username=ssh_user, password=password, timeout=10 )

        print(f"🔧 [{hostname}] Setting up environment...")
        install_cmd = f"wget {RATHOLE_DOWNLOAD_URL} -O /tmp/rathole.zip && unzip -o /tmp/rathole.zip -d /tmp && mv /tmp/rathole /usr/local/bin/ && chmod +x /usr/local/bin/rathole"
        stdin, stdout, stderr = ssh.exec_command(install_cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error_output = stderr.read().decode()
            print(f"⚠️ [{hostname}] Warning: Failed to install rathole (maybe already exists?): {error_output}")
        
        ssh.exec_command("mkdir -p /etc/rathole")
        
        sftp = ssh.open_sftp()
        service_template = env.get_template('rathole.service.j2')

        for config in configs_to_deploy:
            role = config['role']
            content = config['content']
            config_filename = f"{role}.toml"
            service_filename = f"rathole-{role}.service"
            print(f"📄 [{hostname}] Uploading configuration to /etc/rathole/{config_filename}...")
            sftp.putfo(BytesIO(content.encode('utf-8')), f'/etc/rathole/{config_filename}')
            print(f"⚙️ [{hostname}] Setting up systemd service {service_filename}...")
            service_content = service_template.render(role=role, config_filename=config_filename)
            sftp.putfo(BytesIO(service_content.encode('utf-8')), f'/etc/systemd/system/{service_filename}')
            print(f"▶️ [{hostname}] Starting service {service_filename}...")
            ssh.exec_command("systemctl daemon-reload")
            ssh.exec_command(f"systemctl enable {service_filename}")
            ssh.exec_command(f"systemctl restart {service_filename}")
        
        sftp.close()
        print(f"✅ [{hostname}] Deployment successful!")
        return {"hostname": hostname, "status": "success", "roles": [c['role'] for c in configs_to_deploy]}

    except Exception as e:
        # --- 关键修改点 ---
        # 当任何错误发生时，打印完整的错误追溯信息
        print(f"❌❌❌ [{hostname}] An exception occurred during deployment! ❌❌❌")
        traceback.print_exc() # 打印详细的 traceback
        return {"hostname": hostname, "status": "failed", "error": str(e)}
    finally:
        if ssh:
            ssh.close()


async def run_deployment(database):
    print("Starting new deployment run...")
    try:
        servers_query = "SELECT * FROM servers"
        rules_query = "SELECT * FROM forwarding_rules"
        print("Fetching data from database...")
        servers = await database.fetch_all(servers_query)
        rules = await database.fetch_all(rules_query)
        print(f"Found {len(servers)} servers and {len(rules)} rules.")
        
        servers = [dict(s) for s in servers]
        rules = [dict(r) for r in rules]

        print("Generating configurations...")
        configs = _generate_configs(servers, rules)
        print("Configurations generated.")

        results = []
        for server in servers:
            print(f"--- Processing server: {server['alias']} ({server['hostname']}) ---")
            if server['id'] in configs and configs[server['id']]:
                configs_for_this_host = configs[server['id']]
                print(f"Found {len(configs_for_this_host)} config(s) to deploy for this server.")
                result = _deploy_to_host(server, configs_for_this_host)
                results.append(result)
            else:
                print("No configurations to deploy for this server. Skipping.")
        
        print("Deployment run finished.")
        return results
    except Exception as e:
        # --- 关键修改点 ---
        # 增加一个全局的 try...except 来捕获任何意外的错误
        print(f"🔥🔥🔥 An unexpected error occurred in the main deployment runner! 🔥🔥🔥")
        traceback.print_exc()
        # 重新抛出异常，让 FastAPI 知道发生了 500 错误
        raise e
