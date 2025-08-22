# backend/models.py
from pydantic import BaseModel, Field
from typing import Literal, Optional

# --- 用于密码处理的辅助函数 ---
from passlib.context import CryptContext

# 创建一个密码上下文，指定加密算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- API 数据模型 ---

# 创建服务器时，前端需要提交的数据模型
class ServerCreate(BaseModel):
    alias: str
    hostname: str
    ssh_user: str
    ssh_port: int = 22
    ssh_password: Optional[str] = None
    role: Literal['server', 'client', 'both'] # 角色只能是这三个值之一

# 从数据库读取或返回给前端的服务器数据模型
# 注意：我们绝不会把 password_hash 返回给前端
class ServerInfo(BaseModel):
    id: int
    alias: str
    hostname: str
    ssh_user: str
    ssh_port: int
    role: Literal['server', 'client', 'both']
    

# --- 新增 Rule 模型 ---

# 创建规则时，前端需要提交的数据模型
class RuleCreate(BaseModel):
    name: str
    rule_type: Literal['tcp', 'udp'] = 'tcp'
    local_port: int = Field(..., gt=0, lt=65536) # 端口号必须在 1-65535 之间
    remote_port: int = Field(..., gt=0, lt=65536)
    client_id: int
    server_id: int

# 返回给前端的规则信息模型
# 我们希望返回更友好的信息，所以加入了客户端和服务端的主机名
class RuleInfo(BaseModel):
    id: int
    name: str
    rule_type: str
    local_port: int
    remote_port: int
    client_id: int
    server_id: int
    client_hostname: str
    server_hostname: str
    client_alias: str
    server_alias: str
    

class ServerStatus(BaseModel):
    # 使用 Optional，因为单角色的服务器只会有一个状态
    server_status: Optional[str] = None
    client_status: Optional[str] = None
    
    
class ServerLogs(BaseModel):
    logs: str
    