# Release Notes v0.3.0

## 核心变化

- 新增 Docker 一键启动能力
- 前端静态资源已集成到后端交付链路
- Compose 可一键拉起 `api + mysql + redis + minio`
- 修复旧 `infra/.env` 兼容性问题
- 修复默认镜像源与包源在当前网络环境下的构建问题
- 修复 Docker 一键启动与宿主机 MySQL / Redis 端口冲突问题

## 启动方式

```bash
cd /Users/xloser/Owner/Code/VibeCoding/FileHub/infra
docker compose up -d --build
```

## 默认入口

- Web：`http://127.0.0.1:8000/files`
- API：`http://127.0.0.1:8000/api/healthz`
- MinIO Console：`http://127.0.0.1:9001`

## 本版重点

本版不是单纯补丁，而是新增了完整部署形态，适合作为新的次版本发布。

## 验收结果

- Docker 环境最小人工验收：通过
- 验收范围：登录、文件夹、上传、预览、下载、回收站、后台管理、日志页
- 发布结论：可进入正式发布闭环
