# 第 39 轮 Docker 一键启动问题根因分析

## 问题 1：`docker compose up -d --build` 提示大量变量未设置

- 问题现象：
  - 启动时提示 `REDIS_DB`、`ADMIN_PASSWORD`、`MINIO_BUCKET`、`APP_PORT` 等变量未设置。
- 可能原因：
  - `infra/.env` 是旧版本，缺少新增加的变量。
  - `docker-compose.yml` 对这些变量没有提供默认值。
  - 文档里用了 `cp -n .env.example .env`，如果本地已存在旧 `.env`，不会被覆盖更新。
- 验证步骤：
  - 检查当前 `infra/.env` 内容。
  - 对比 `infra/.env.example` 新增字段。
  - 检查 `infra/docker-compose.yml` 中变量引用方式。
- 验证结果：
  - 当前 `infra/.env` 只包含 MySQL、Redis 端口和 MinIO 基础项，缺失 `APP_PORT`、`REDIS_DB`、`MINIO_BUCKET`、`JWT_SECRET`、管理员账号相关变量。
  - `docker-compose.yml` 中直接使用 `${VAR}`，未提供默认值，因此旧 `.env` 会触发警告。
- 最终根因：
  - Compose 配置对新增变量缺少默认值，且旧 `.env` 会被 `cp -n` 保留下来，导致一键启动对历史配置不兼容。
- 修复方案：
  - 为 Compose 中所有新增变量补默认值 `${VAR:-default}`。
  - 保持旧 `.env` 也能直接启动，不再依赖手工同步新字段。

## 问题 2：构建阶段拉取 `node:20-alpine` 返回 403 Forbidden

- 问题现象：
  - 构建应用镜像时，`load metadata for docker.io/library/node:20-alpine` 返回 `403 Forbidden`。
- 可能原因：
  - 当前环境直接访问 Docker Hub 受限。
  - 一键启动默认使用 Docker Hub 官方源，对当前网络环境不友好。
  - 即使基础镜像可拉取，后续 `npm ci`、`pip install` 也可能继续受默认国外源影响。
- 验证步骤：
  - 检查 `backend/Dockerfile` 的基础镜像来源。
  - 检查 Compose 中 MySQL、Redis、MinIO 的镜像来源。
- 验证结果：
  - `backend/Dockerfile` 直接使用 `node:20-alpine`、`python:3.12-slim`。
  - `docker-compose.yml` 直接使用 `mysql:8.4`、`redis:7.2`、`minio/minio:latest`。
  - 这些都默认走 Docker Hub。
- 最终根因：
  - Docker 一键启动默认依赖 Docker Hub 和默认 npm/pip 源，不适合当前网络环境，导致镜像元数据拉取阶段直接失败。
- 修复方案：
  - 为 Dockerfile 和 Compose 引入镜像源默认值，默认使用 `docker.m.daocloud.io`。
  - 在 Dockerfile 中把 npm 和 pip 默认源切到国内镜像，降低构建阶段失败概率。

## 结论

这次不是应用代码逻辑错误，而是 Docker 交付层对“旧 `.env` 兼容性”和“当前网络环境”考虑不足。修复重点应放在：

1. Compose 变量默认值补齐。
2. Docker 镜像源和包源默认切到更可用的镜像。
3. 文档明确旧 `.env` 兼容策略和可覆盖的镜像源参数。
