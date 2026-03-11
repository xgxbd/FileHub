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
- `DELETE /files/{file_id}`：软删除文件（移入回收站）
- `GET /files/{file_id}/download`：下载文件（支持 `Range` 断点续传）
- `GET /files/{file_id}/preview`：在线预览（支持 `image/*`、`application/pdf`、`text/*`）

## 回收站 MVP 接口

- `GET /recycle/files`：获取回收站文件列表（需 Bearer Token）
- `POST /recycle/files/{file_id}/restore`：恢复回收站文件
- `DELETE /recycle/files/{file_id}/purge`：彻底删除回收站文件

## 操作日志 MVP 接口

- `GET /admin/logs`：管理员查询操作日志（需 Bearer Token，且角色为 `admin`）
  - 支持参数：`action`、`user_id`、`start_at`、`end_at`、`page`、`page_size`

## 管理端文件管理 MVP 接口

- `GET /admin/files`：管理员查询全量文件
  - 支持参数：`owner_id`、`keyword`、`status(active/deleted/all)`、`page`、`page_size`

## 分片上传 MVP 接口

- `POST /upload/sessions`：创建上传会话
- `GET /upload/sessions/{upload_id}`：查询会话状态（已上传分片）
- `PUT /upload/sessions/{upload_id}/chunks/{chunk_index}`：上传单个分片
- `POST /upload/sessions/{upload_id}/complete`：合并分片并完成入库

## 最小验证

```bash
cd backend
source .venv/bin/activate
python -m pip install -r requirements.txt
pytest -q
```

## 管理员初始化（第十轮）

- 通过环境变量控制启动自动初始化：
  - `ADMIN_BOOTSTRAP_ENABLED=true`
  - `ADMIN_EMAIL`、`ADMIN_USERNAME`、`ADMIN_PASSWORD`
- 启动时若账号不存在会自动创建；已存在则仅校正为 `admin` 角色（不重置密码）
- 建议验证命令：
  ```bash
  cd backend
  source .venv/bin/activate
  ADMIN_BOOTSTRAP_ENABLED=true \
  ADMIN_EMAIL=admin@example.com \
  ADMIN_USERNAME=admin \
  ADMIN_PASSWORD='StrongPassw0rd!' \
  python scripts/check_admin_bootstrap.py
  ```

## 质量基线脚本（第十二轮）

- 主链路烟雾验证：
  ```bash
  cd backend
  source .venv/bin/activate
  python scripts/smoke_core_flow.py
  ```
- 轻量性能基线：
  ```bash
  cd backend
  source .venv/bin/activate
  python scripts/perf_baseline.py
  ```

## 告警治理（第十四轮）

- 应用生命周期已从 `on_event("startup")` 迁移至 `lifespan`
- Range 下载接口已使用 `HTTP_416_RANGE_NOT_SATISFIABLE` 常量

## 认证哈希迁移（第十五轮）

- 密码哈希与校验已从 `passlib` 迁移为 `bcrypt` 原生实现
- `requirements.txt` 已移除 `passlib[bcrypt]`
- 兼容性保障：既有 bcrypt 哈希账号可继续登录（见 `test_auth_api.py`）
