# FileHub 发布清单

## v0.3.0 发布执行结果

### 1. 代码与分支

- [x] 目标发布分支来自 `release/v0.3.0`
- [x] 所有 Docker 交付相关 feature 已合并进入 `develop`
- [x] `docs/PROGRESS.md` 已更新到发布闭环
- [x] 提交信息均为中文自然语言且可追溯

### 2. 自动化与构建

- [x] 应用镜像已实际构建成功：`docker compose build api`
- [x] Docker 一键启动已实际通过：`docker compose up -d --build`
- [x] 健康检查通过：`http://127.0.0.1:8000/api/healthz`
- [x] 前端页面入口可达：`http://127.0.0.1:8000/files`

### 3. 人工验收

- [x] 登录通过
- [x] 文件夹操作通过
- [x] 上传通过
- [x] 预览通过
- [x] 下载通过
- [x] 回收站通过
- [x] 后台管理通过
- [x] 日志页通过

### 4. 发布动作

- [x] `release/v0.3.0` 已合并到 `main`
- [x] `release/v0.3.0` 已回合并到 `develop`
- [x] 标签 `v0.3.0` 已创建并推送
- [x] `main`、`develop`、`release/v0.3.0` 已同步远端

### 5. 当前结论

- [x] `v0.3.0` 已正式交付

---

## 通用模板（后续版本复用）

## 1. 代码与分支

- [ ] 目标发布分支来自 `release/*`（由 `develop` 切出）
- [ ] 所有 feature 分支已合并，`develop` 状态稳定
- [ ] `docs/PROGRESS.md` 已更新到最新轮次
- [ ] 提交信息均为中文自然语言且可追溯

## 2. 后端验证

- [ ] 虚拟环境可用：`cd backend && source .venv/bin/activate`
- [ ] 单元/集成测试通过：`APP_SERVE_FRONTEND=false pytest -q`
- [ ] 烟雾脚本通过：`APP_SERVE_FRONTEND=false python scripts/smoke_core_flow.py`
- [ ] 性能基线已采集：`APP_SERVE_FRONTEND=false python scripts/perf_baseline.py`
- [ ] 本轮验证结果已记录（当前基线：`44 passed`）

## 3. 前端验证

- [ ] 构建通过：`cd frontend && npm run build`
- [ ] 前端 E2E 通过：`cd frontend && npm run e2e`
- [ ] 后端托管前端 E2E 通过：`cd frontend && npm run e2e:hosted`
- [ ] 管理员页面可访问：`/admin/files`、`/admin/logs`
- [ ] 用户页面可访问：`/files`、`/recycle`

## 4. 配置与安全

- [ ] 生产环境替换 `JWT_SECRET`
- [ ] 若启用管理员初始化，已替换 `ADMIN_PASSWORD`
- [ ] MinIO/Redis/MySQL 连接参数已按环境配置
- [ ] `.env` 文件不包含无效占位值

## 5. 发布动作

- [ ] 打 tag 前确认版本说明
- [ ] 发布后执行一次核心链路人工验收（登录/上传/下载/回收/日志）
- [ ] 监控启动并记录发布时间点

## 6. 推荐执行顺序

```bash
cd backend
source .venv/bin/activate
APP_SERVE_FRONTEND=false pytest -q
APP_SERVE_FRONTEND=false python scripts/smoke_core_flow.py
APP_SERVE_FRONTEND=false python scripts/perf_baseline.py

cd ../frontend
npm run build
npm run e2e
npm run e2e:hosted
```

预期口径：

- 后端测试全部通过。
- 常规前端 E2E 全部通过。
- 后端托管前端 smoke 通过。
- `/files`、`/upload`、`/preview`、`/recycle`、`/admin/files`、`/admin/logs` 都可达。
- `npm run e2e` 与 `npm run e2e:hosted` 需要顺序执行，避免端口冲突。
