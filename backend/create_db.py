# backend/create_db.py
from database import engine, metadata

print("正在创建数据库表...")
# SQLAlchemy 会检查表是否存在，如果不存在则创建
metadata.create_all(bind=engine)
print("数据库表创建成功！")