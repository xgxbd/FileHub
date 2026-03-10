# FileHub

FileHub 是一个从零开始构建的 Web 文件仓库系统，目标是提供“上传-管理-下载-回收-审计”的完整闭环能力。

## 当前阶段

- 已建立 GitFlow 基线分支：`main`、`develop`、`feature/*`
- 已完成认证、文件列表、分片上传、断点续传下载、文件预览与回收站 MVP 能力

## 技术栈

- 前端：Vue 3 + PrimeVue
- 后端：FastAPI
- 数据与存储：MySQL + Redis + MinIO

## 快速启动（骨架阶段）

1. 启动基础中间件（可选）：
   ```bash
   cd infra
   cp -n .env.example .env
   docker compose up -d
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

## 当前可验证内容

- 后端健康检查：`GET /healthz`
- 前端骨架页面：`/`
- 前端通过 `/api/healthz` 代理请求后端健康接口
- 前端构建命令：`npm run build`

## 开发约束

- 仅允许在项目虚拟环境中运行 Python
- 每个最小可验证改动独立提交，提交信息为具体中文自然语言
- 每次任务完成都更新 `docs/PROGRESS.md`
