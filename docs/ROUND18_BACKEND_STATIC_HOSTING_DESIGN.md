# ROUND18 前端 Build 后由后端托管实施设计

## 1. 目标
- 实现“前端先 build，后端统一托管页面与 API”。
- 启动方式支持仅启动 FastAPI 后端即可访问 Web 页面。

## 2. 约束与边界
- 保持现有前端接口调用前缀 `/api` 不变。
- 不影响当前开发期双进程模式（Vite + FastAPI）。
- 以开关方式启用，避免一次性破坏现有测试与联调流程。

## 3. 路由策略
- 启用托管模式时：
  - API 仅挂载到 `/api/*`。
  - 前端静态资源从 `frontend/dist` 提供。
  - 非 `/api/*` 路径走 SPA 回退到 `index.html`。
- 未启用托管模式时：
  - 保持现状，后端继续直接暴露原 API 路径，前端通过 Vite 代理联调。

## 4. 配置方案
- 新增配置：`APP_SERVE_FRONTEND`（默认 `false`）。
- 新增配置：`FRONTEND_DIST_DIR`（默认自动定位 `../frontend/dist`）。

## 5. 最小提交拆分
- 提交 A：本设计文档。
- 提交 B：后端接入静态托管与 SPA 回退（含 `/api` 路由切换逻辑）。
- 提交 C：文档与启动说明更新（单后端模式命令、注意事项）。

## 6. 验收标准
- `APP_SERVE_FRONTEND=true` 且前端已 build 时，启动后端可访问页面。
- 页面刷新任意前端路由（如 `/files`）不会 404。
- 前端接口调用正常命中 `/api/*`。
- `APP_SERVE_FRONTEND=false` 时，现有开发链路不变。
