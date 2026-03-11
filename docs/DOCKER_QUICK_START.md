# Docker 一键启动

## 目标

通过一条命令启动完整 FileHub：

```bash
cd infra
docker compose up -d --build
```

## 启动步骤

前置条件：

- 已安装 Docker
- Docker daemon 已启动

### 1. 准备 Compose 环境变量

```bash
cd /Users/xloser/Owner/Code/VibeCoding/FileHub/infra
cp -n .env.example .env
```

如需修改端口或管理员账号，编辑 `infra/.env`。

### 2. 启动完整系统

```bash
cd /Users/xloser/Owner/Code/VibeCoding/FileHub/infra
docker compose up -d --build
```

### 3. 验证

- Web：`http://127.0.0.1:8000/files`
- API：`http://127.0.0.1:8000/api/healthz`
- MinIO Console：`http://127.0.0.1:9001`

### 4. 查看状态

```bash
cd /Users/xloser/Owner/Code/VibeCoding/FileHub/infra
docker compose ps
docker compose logs -f api
```

### 5. 停止

```bash
cd /Users/xloser/Owner/Code/VibeCoding/FileHub/infra
docker compose down
```

## 当前持久化位置

Docker Compose 使用命名卷保存数据：

- `mysql_data`
- `redis_data`
- `minio_data`
- `backend_tmp_data`

说明：

- MySQL 元数据保存在 `mysql_data`
- Redis 持久化数据保存在 `redis_data`
- MinIO 对象保存在 `minio_data`
- 应用上传临时文件和本地对象兜底副本保存在 `backend_tmp_data`

## 设计说明

- 前端在镜像构建阶段自动执行 `npm run build`
- 后端容器启动后直接托管前端静态资源
- 应用容器通过 Compose 服务名访问 `mysql`、`redis`、`minio`
