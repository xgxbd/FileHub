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
