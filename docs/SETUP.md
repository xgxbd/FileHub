# 本地开发初始化（P0）

## 1. GitFlow 分支规则

- 主分支：`main`
- 集成分支：`develop`
- 功能开发：从 `develop` 拉取 `feature/*`

## 2. 启动基础依赖服务

```bash
cd infra
cp .env.example .env
docker compose up -d mysql redis minio
```

服务说明：

- MySQL: `127.0.0.1:3306`
- Redis: `127.0.0.1:6379`
- MinIO API: `127.0.0.1:9000`
- MinIO Console: `http://127.0.0.1:9001`

## 2.1 一键启动完整系统（Docker Compose）

如果你要直接启动完整的 FileHub Web 系统，而不是只起中间件，使用下面这组命令：

前置条件：

- 已安装 Docker
- Docker daemon 已启动（例如 Docker Desktop 已运行）

```bash
cd infra
cp -n .env.example .env
docker compose up -d --build
```

启动后可直接访问：

- Web：`http://127.0.0.1:8000/files`
- API 健康检查：`http://127.0.0.1:8000/api/healthz`
- MinIO Console：`http://127.0.0.1:9001`

默认管理员账号取自 `infra/.env`：

- 用户名：`ADMIN_USERNAME`
- 密码：`ADMIN_PASSWORD`

常用命令：

```bash
cd infra
docker compose ps
docker compose logs -f api
docker compose down
```

## 3. 后端虚拟环境规范（必须）

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

禁止使用系统 Python 安装依赖，禁止全局安装第三方包。

## 4. 单后端托管前端（可选）

如果希望只启动后端，同时直接访问前端页面，可使用以下模式：

1. 构建前端

```bash
cd frontend
npm install
npm run build
```

2. 启用后端托管

```bash
cd backend
cp -n .env.example .env
```

在 `.env` 中设置：

```env
APP_SERVE_FRONTEND=true
# 可选：自定义前端 dist 目录，不填则默认定位 ../frontend/dist
FRONTEND_DIST_DIR=
```

3. 启动后端

```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

4. 验证

- 页面入口：`http://127.0.0.1:8000/files`
- API 入口：`http://127.0.0.1:8000/api/healthz`

## 5. 发布前最小验证命令

### 后端全量测试

```bash
cd backend
source .venv/bin/activate
APP_SERVE_FRONTEND=false pytest -q
```

### 前端常规 E2E

```bash
cd frontend
npm run e2e
```

### 后端托管前端 E2E

```bash
cd frontend
npm run e2e:hosted
```

说明：

- `npm run e2e`：验证前后端分离开发模式。
- `npm run e2e:hosted`：先构建前端，再由后端托管静态资源，验证最终交付形态。
