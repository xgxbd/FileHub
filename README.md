# FileHub

FileHub 是一个从零开始构建的 Web 文件仓库系统，目标是提供“上传-管理-下载-回收-审计”的完整闭环能力。

## 当前交付状态

- 当前正式交付版本：`v0.3.0`
- 当前发布主分支：`main`
- 已支持 Docker 一键启动完整系统
- 已完成认证、文件树、分片上传、下载、预览、回收站、管理端、操作日志 MVP 能力
- 已完成 Docker 形态人工验收并发布

相关文档：

- 发布说明：[docs/RELEASE_NOTES_v0.3.0.md](/Users/xloser/Owner/Code/VibeCoding/FileHub/docs/RELEASE_NOTES_v0.3.0.md)
- Docker 快速启动：[docs/DOCKER_QUICK_START.md](/Users/xloser/Owner/Code/VibeCoding/FileHub/docs/DOCKER_QUICK_START.md)
- Docker 验收清单：[docs/RELEASE_v0.3.0_DOCKER_ACCEPTANCE.md](/Users/xloser/Owner/Code/VibeCoding/FileHub/docs/RELEASE_v0.3.0_DOCKER_ACCEPTANCE.md)

## 技术栈

- 前端：Vue 3 + PrimeVue
- 后端：FastAPI
- 数据与存储：MySQL + Redis + MinIO

## 推荐启动方式（Docker 一键交付）

```bash
cd infra
cp -n .env.example .env
docker compose up -d --build
```

访问：

- Web：`http://127.0.0.1:8000/files`
- API：`http://127.0.0.1:8000/api/healthz`
- MinIO Console：`http://127.0.0.1:9001`

默认管理员账号：

- 用户名：`admin`
- 密码：`ChangeMe123!`

## 开发模式（双进程）

1. 启动基础中间件（可选）：
   ```bash
   cd infra
   cp -n .env.example .env
   docker compose up -d mysql redis minio
   ```
2. 启动后端（仅虚拟环境）：
   ```bash
   cd backend
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp -n .env.example .env
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
3. 启动前端：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 单后端托管模式（非 Docker，可选）

1. 构建前端静态资源：
   ```bash
   cd frontend
   npm install
   npm run build
   ```
2. 启动后端托管模式：
   ```bash
   cd backend
   source .venv/bin/activate
   cp -n .env.example .env
   # 在 .env 中设置 APP_SERVE_FRONTEND=true
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
3. 访问：
   - Web 页面：`http://127.0.0.1:8000/files`
   - API：`http://127.0.0.1:8000/api/*`

## 当前可验证内容

- Docker 一键启动完整系统
- 后端健康检查：`GET /api/healthz`
- 文件列表页：`/files`
- 管理页：`/admin/files`
- 日志页：`/admin/logs`
- Docker 形态下登录、上传、下载、预览、回收、日志链路已人工验收通过

## 开发约束

- 仅允许在项目虚拟环境中运行 Python
- 每个最小可验证改动独立提交，提交信息为具体中文自然语言
- 每次任务完成都更新 `docs/PROGRESS.md`
