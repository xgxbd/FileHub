# 本地开发初始化（P0）

## 1. GitFlow 分支规则

- 主分支：`main`
- 集成分支：`develop`
- 功能开发：从 `develop` 拉取 `feature/*`

## 2. 启动基础依赖服务

```bash
cd infra
cp .env.example .env
docker compose up -d
```

服务说明：

- MySQL: `127.0.0.1:3306`
- Redis: `127.0.0.1:6379`
- MinIO API: `127.0.0.1:9000`
- MinIO Console: `http://127.0.0.1:9001`

## 3. 后端虚拟环境规范（必须）

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

禁止使用系统 Python 安装依赖，禁止全局安装第三方包。

