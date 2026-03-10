# FileHub 发布清单（MVP）

## 1. 代码与分支

- [ ] 目标发布分支来自 `release/*`（由 `develop` 切出）
- [ ] 所有 feature 分支已合并，`develop` 状态稳定
- [ ] `docs/PROGRESS.md` 已更新到最新轮次
- [ ] 提交信息均为中文自然语言且可追溯

## 2. 后端验证

- [ ] 虚拟环境可用：`cd backend && source .venv/bin/activate`
- [ ] 单元/集成测试通过：`pytest -q`
- [ ] 烟雾脚本通过：`python scripts/smoke_core_flow.py`
- [ ] 性能基线已采集：`python scripts/perf_baseline.py`

## 3. 前端验证

- [ ] 构建通过：`cd frontend && npm run build`
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
