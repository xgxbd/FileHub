# Round 2 认证模块 MVP 设计（先设计后实现）

## 1. 目标与边界

- 目标：实现认证最小闭环，覆盖注册、登录、刷新令牌、获取当前用户。
- 边界：本轮只做后端能力，不做登录页完整 UI 还原。
- 角色：仅支持 `user`、`admin` 两种角色字段，权限细化后置。

## 2. 模块划分

### 2.1 后端模块

- `app/db/`：数据库引擎、会话、基础模型。
- `app/models/user.py`：用户元数据模型。
- `app/schemas/auth.py`：认证请求/响应模型。
- `app/services/security.py`：密码哈希校验、JWT 生成与解析。
- `app/services/auth_service.py`：注册、登录、刷新核心流程。
- `app/api/auth.py`：认证接口。
- `app/api/deps.py`：鉴权依赖，提供 `get_current_user`。

### 2.2 数据与缓存

- MySQL（元数据）：`users` 表存用户账号信息与状态。
- Redis（会话）：存 refresh token 的 `jti` 与 TTL，用于刷新链路最小防重放。
- 本地开发默认可用 SQLite（仅开发便利）；生产配置使用 MySQL DSN。

## 3. 数据结构设计

### 3.1 users 表（MVP）

- `id` bigint PK
- `email` varchar(255) unique not null
- `username` varchar(64) unique not null
- `password_hash` varchar(255) not null
- `role` varchar(16) not null default `user`
- `is_active` bool not null default true
- `created_at` datetime not null
- `updated_at` datetime not null

### 3.2 Redis Key 设计

- `auth:refresh:{jti}` -> `{"uid": <user_id>, "token_version": 1}`
- TTL：`JWT_REFRESH_EXPIRE_DAYS * 24h`

## 4. 接口设计（MVP）

- `POST /auth/register`
  - 入参：`email`, `username`, `password`
  - 出参：`user_id`, `email`, `username`
- `POST /auth/login`
  - 入参：`account`, `password`（account 支持邮箱或用户名）
  - 出参：`access_token`, `refresh_token`, `token_type`, `expires_in`
- `POST /auth/refresh`
  - 入参：`refresh_token`
  - 出参：新 `access_token` 与 `refresh_token`
- `GET /auth/me`
  - Header：`Authorization: Bearer <access_token>`
  - 出参：当前用户基础信息

## 5. 安全策略（MVP）

- 密码哈希：`passlib[bcrypt]`。
- Token：JWT（`HS256`），区分 `type=access|refresh`。
- Access 短期有效，Refresh 长期有效。
- 刷新时校验 Redis 中 `jti` 是否存在，不存在则拒绝。

## 6. 最小提交拆分与验证

### 提交 A（设计）
- 内容：新增本设计文档与任务拆分。
- 验证：文档可评审，范围与接口清晰。

### 提交 B（数据与配置骨架）
- 内容：新增 DB 会话、基础模型、`users` 模型、配置项扩展。
- 验证：`python -c "from app.models.user import User"` 成功。

### 提交 C（安全与服务层）
- 内容：密码与 JWT 工具、Redis refresh 会话存取抽象。
- 验证：`python -c` 生成并解析 token 成功。

### 提交 D（认证接口）
- 内容：注册/登录/刷新/me 路由与依赖接入主路由。
- 验证：`TestClient` 跑通注册->登录->me 的最小流程脚本。

### 提交 E（测试与文档收口）
- 内容：新增基础测试与 README 更新。
- 验证：测试脚本通过；文档包含运行与验收步骤。

## 7. 非目标（本轮不做）

- 邮箱验证码、找回密码、登录风控、设备管理、SSO/OAuth。
- 细粒度 RBAC 与权限策略中心。
