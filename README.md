# Rathole Manager

Rathole Manager 是一个用于管理 `rathole` 反向代理工具的 Web UI。它允许用户通过图形化界面轻松地添加服务器、定义转发规则，并将配置一键部署到远程服务器上。

## ✨ 功能特性

- **Web 管理界面**: 通过浏览器即可管理所有服务器和规则。
- **服务器管理**: 添加、编辑、删除将要运行 `rathole` 的服务器节点。
- **规则定义**: 灵活定义 TCP/UDP 转发规则，关联客户端与服务端。
- **一键部署**: 自动将 `rathole` 服务端和客户端的配置推送到指定的远程服务器。
- **自动安装**: 在部署时会自动在目标服务器上下载并安装 `rathole` 程序。
- **服务管理**: 自动创建并管理远程服务器上的 `systemd` 服务，实现开机自启和进程守护。
- **状态监控**: 查看远程 `rathole` 服务的运行状态和日志。
- **安全存储**: 使用加密方式存储服务器的 SSH 凭据。

## 🛠️ 技术栈

- **后端**: Python 3, FastAPI, SQLAlchemy, Paramiko
- **前端**: Vue.js, Vite, Pinia, Axios
- **数据库**: SQLite

## 🚀 快速开始

### 先决条件

- Python 3.11+
- Node.js 18+ 和 npm

### 后端设置

1.  **进入后端目录**
    ```bash
    cd backend
    ```

2.  **创建并激活虚拟环境**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

4.  **创建数据库**
    (该项目包含一个 `create_db.py` 脚本来初始化数据库)
    ```bash
    python create_db.py
    ```

5.  **运行后端服务**
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
    API 将在 `http://localhost:8000` 上可用。

### 前端设置

1.  **进入前端目录**
    ```bash
    cd frontend
    ```

2.  **安装依赖**
    ```bash
    npm install
    ```

3.  **运行开发服务器**
    ```bash
    npm run dev
    ```
    Web 界面将在 `http://localhost:5173` (或另一个可用端口) 上可用。

## ⚙️ 配置

为了安全，`backend/security.py` 中用于加密密码的 `SECRET_KEY` 不应硬编码。在生产环境中，强烈建议从环境变量中读取它。

```python
# backend/security.py
import os

# 从环境变量获取密钥，如果不存在则使用默认值（仅用于开发）
SECRET_KEY = os.environ.get('RATHOLE_MANAGER_SECRET_KEY', 'pzsZzVd-hizgDy_u-M9Ypm2y2x41gT8m5eL2t_G2gPY=').encode()
```

## 📝 API 概览

- `GET /api/servers`: 获取所有服务器列表
- `POST /api/servers`: 添加一个新服务器
- `GET /api/rules`: 获取所有转发规则
- `POST /api/rules`: 添加一条新规则
- `POST /api/deploy`: 触发部署流程，将配置应用到所有服务器
- `GET /api/servers/{id}/status`: 获取指定服务器上 `rathole` 服务的状态
- `GET /api/servers/{id}/logs`: 获取指定 `rathole` 服务的日志
- `POST /api/servers/{id}/uninstall`: 卸载指定服务器上的 `rathole` 服务
