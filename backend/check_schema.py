# backend/check_schema.py
from sqlalchemy import create_engine, inspect

# 确保这里的数据库URL和你的database.py里的一致
DATABASE_URL = "sqlite:///./rathole_manager.db"
engine = create_engine(DATABASE_URL)

print("--- 正在检查数据库 schema ---")
try:
    inspector = inspect(engine)

    print("\n[+] 存在的表 (Tables):")
    print(inspector.get_table_names())

    if 'servers' in inspector.get_table_names():
        print("\n[+] 'servers' 表的字段 (Columns):")
        columns = inspector.get_columns('servers')
        for column in columns:
            print(f"- {column['name']} (Type: {column['type']})")
    else:
        print("\n[-] 错误: 'servers' 表不存在!")

except Exception as e:
    print(f"\n[!] 检查时发生错误: {e}")

print("\n--- 检查完毕 ---")