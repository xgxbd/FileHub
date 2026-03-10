# backend

后端工程目录（FastAPI）。

## Python 运行规范

仅允许项目虚拟环境：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

禁止修改系统 Python，禁止全局安装依赖。

## 最小运行（本轮骨架）

```bash
cd backend
cp .env.example .env
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

健康检查接口：

- `GET http://127.0.0.1:8000/healthz`

## 认证 MVP 接口

- `POST /auth/register`：注册
- `POST /auth/login`：登录
- `POST /auth/refresh`：刷新令牌
- `GET /auth/me`：当前用户信息（Bearer Token）

## 文件列表 MVP 接口

- `GET /files`：获取文件列表（需 Bearer Token）
  - 支持参数：`keyword`、`min_size`、`max_size`、`page`、`page_size`
  - 普通用户仅返回自己的文件，管理员返回全部文件

## 最小验证

```bash
cd backend
source .venv/bin/activate
python -m pip install -r requirements.txt
pytest -q
```
