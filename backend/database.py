# backend/database.py
import sqlalchemy
from databases import Database

# 数据库文件名为 rathole_manager.db
DATABASE_URL = "sqlite:///./rathole_manager.db"

# 创建一个 Database 实例，用于 FastAPI 进行异步操作
database = Database(DATABASE_URL)

# SQLAlchemy 的核心，用于与数据库进行交互
engine = sqlalchemy.create_engine(DATABASE_URL)

# 元数据，用于存放所有表的定义
metadata = sqlalchemy.MetaData()

# 定义 "servers" 表的结构
servers = sqlalchemy.Table(
    "servers",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("alias", sqlalchemy.String, unique=True, index=True),
    sqlalchemy.Column("hostname", sqlalchemy.String, unique=True, index=True),
    sqlalchemy.Column("ssh_user", sqlalchemy.String),
    sqlalchemy.Column("ssh_port", sqlalchemy.Integer, default=22),
    sqlalchemy.Column("encrypted_password", sqlalchemy.String),
    sqlalchemy.Column("role", sqlalchemy.String),
)


forwarding_rules = sqlalchemy.Table(
    "forwarding_rules",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False), # 规则的别名, 例如 "我的网站"
    sqlalchemy.Column("rule_type", sqlalchemy.String, default="tcp"), # 'tcp' or 'udp'
    sqlalchemy.Column("local_port", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("remote_port", sqlalchemy.Integer, nullable=False),
    # 定义外键，关联到 servers 表的 id 字段
    sqlalchemy.Column("client_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("servers.id")),
    sqlalchemy.Column("server_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("servers.id")),
)

# 使用 create_all 来创建数据库和表 (我们会在一个单独的脚本中调用)
# metadata.create_all(engine)