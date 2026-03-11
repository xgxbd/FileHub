# FileHub

FileHub 是一个从零开始构建的 Web 文件仓库系统，目标是提供“上传-管理-下载-回收-审计”的完整闭环能力。

## 当前阶段

- 已建立 GitFlow 基线分支：`main`、`develop`、`feature/*`
- 已完成认证、文件列表、分片上传、断点续传下载、文件预览、回收站与操作日志 MVP 能力
- 已提供管理员启动初始化能力（基于环境变量自动创建/校正管理员）
- 已提供管理端文件管理页（管理员全量视图与状态操作）
- 已提供发布前质量基线脚本与发布/回滚清单文档
- 已补齐前端关键流程 E2E 自动化（登录/上传/下载/删除/恢复）
- 已完成关键告警治理与前端分包优化（第十四轮）
- 已完成认证哈希实现迁移（passlib -> bcrypt）并清理相关弃用告警

## 技术栈

- 前端：Vue 3 + PrimeVue
- 后端：FastAPI
- 数据与存储：MySQL + Redis + MinIO

## 快速启动（双进程开发模式）

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

## 单后端启动模式（前端先 build，再由后端托管）

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

- 后端健康检查：`GET /healthz`
- 前端骨架页面：`/`
- 前端通过 `/api/healthz` 代理请求后端健康接口
- 前端构建命令：`npm run build`
- 单后端托管模式下可直接访问前端页面与 `/api/*`

## 开发约束

- 仅允许在项目虚拟环境中运行 Python
- 每个最小可验证改动独立提交，提交信息为具体中文自然语言
- 每次任务完成都更新 `docs/PROGRESS.md`
