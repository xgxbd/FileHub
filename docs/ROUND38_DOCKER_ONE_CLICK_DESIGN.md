# 第 38 轮 Docker 一键启动实施设计

## 目标

把当前 FileHub 从“本地手工启动前后端 + 单独启动中间件”改造成“单条命令即可启动完整系统”的交付形态。

目标命令：

```bash
cd infra
docker compose up -d --build
```

启动后直接访问：

- Web：`http://127.0.0.1:8000/files`
- MinIO Console：`http://127.0.0.1:9001`

## 当前问题

1. 现有 `infra/docker-compose.yml` 只编排 MySQL、Redis、MinIO，没有应用服务。
2. 仓库没有前后端 Dockerfile，无法构建镜像。
3. 后端 `.env.example` 默认走 MySQL，但 `requirements.txt` 缺少 `pymysql`，容器内无法连接 MySQL。
4. 当前“后端托管前端”依赖本地先手动 `npm run build`，不满足一键启动。

## 设计原则

1. 继续沿用“后端托管前端静态资源”的最终交付形态。
2. 只增加一个应用容器 `api`，不额外拆分 `web` 容器，避免过度设计。
3. Docker Compose 仍保留 MySQL、Redis、MinIO，满足既定技术栈。
4. 默认启用卷持久化，避免容器重建后数据丢失。

## 容器拓扑

- `mysql`
  - 存储业务元数据
- `redis`
  - 存储上传会话、分片状态、缓存
- `minio`
  - 存储文件对象内容
- `api`
  - 运行 FastAPI
  - 在镜像构建阶段编译 Vue 前端
  - 运行时由 FastAPI 托管 `frontend/dist`

## 镜像设计

采用单 Dockerfile 多阶段构建：

### 阶段 1：前端构建阶段

- 基础镜像：`node:20-alpine`
- 工作目录：`/app/frontend`
- 安装前端依赖
- 执行 `npm run build`
- 产出：`frontend/dist`

### 阶段 2：后端运行阶段

- 基础镜像：`python:3.12-slim`
- 工作目录：`/app/backend`
- 安装后端依赖
- 拷贝 `backend/` 源码
- 拷贝上一阶段的 `frontend/dist` 到 `/app/frontend/dist`
- 启动命令：

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Compose 设计

在 `infra/docker-compose.yml` 增加 `api` 服务：

- `build.context: ..`
- `dockerfile: backend/Dockerfile`
- `depends_on`：`mysql`、`redis`、`minio`
- `ports`：`8000:8000`
- 关键环境变量：
  - `APP_SERVE_FRONTEND=true`
  - `FRONTEND_DIST_DIR=/app/frontend/dist`
  - `DATABASE_URL=mysql+pymysql://filehub:filehub_dev_password@mysql:3306/filehub`
  - `REDIS_HOST=redis`
  - `MINIO_ENDPOINT=minio:9000`
  - `UPLOAD_TMP_DIR=/app/backend/tmp/uploads`

## 持久化设计

保留并扩展卷：

- `mysql_data:/var/lib/mysql`
- `redis_data:/data`
- `minio_data:/data`
- `backend_tmp_data:/app/backend/tmp`

说明：
- `backend_tmp_data` 用于持久化上传临时文件和本地对象兜底副本。
- 即使 MinIO 临时不可用，开发环境也不会立刻丢失文件对象。

## 依赖修正

后端依赖新增：

- `pymysql`

原因：
- 当前 `DATABASE_URL` 使用的是 `mysql+pymysql://...`
- 不补驱动，应用容器无法连接 MySQL

## 配置文件设计

### `infra/.env.example`

继续作为 Compose 启动的主配置文件，新增：

- `APP_PORT=8000`
- `ADMIN_BOOTSTRAP_ENABLED=true`
- `ADMIN_USERNAME=admin`
- `ADMIN_PASSWORD=ChangeMe123!`
- `JWT_SECRET=change_me_in_production`

### `backend/.env.example`

保留本地 venv 开发用途，不作为 Docker 一键启动主入口。

## 验收标准

### 配置验收

```bash
cd infra
docker compose config
```

应成功输出完整服务配置。

### 运行验收

```bash
cd infra
docker compose up -d --build
```

应满足：

1. `http://127.0.0.1:8000/files` 可访问。
2. `http://127.0.0.1:8000/api/healthz` 返回 `status=ok`。
3. `http://127.0.0.1:9001` 可访问 MinIO Console。
4. 管理员账号可用。

## 最小提交拆分

### 提交 1：设计冻结

- 新增本设计文档

### 提交 2：补应用镜像构建能力

- 新增 `backend/Dockerfile`
- 新增根目录 `.dockerignore`
- 后端依赖补 `pymysql`

### 提交 3：补 Compose 应用服务与一键启动文档

- 更新 `infra/docker-compose.yml`
- 更新 `infra/.env.example`
- 更新启动文档
- 增加 Docker 一键启动说明

### 提交 4：做最小可验证校验并收口

- 运行 `docker compose config`
- 如环境允许，执行 `docker compose build api`
- 更新 `docs/PROGRESS.md`
