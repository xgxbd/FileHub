# FileHub v0.1.0 发布说明

发布日期：2026-03-11（候选）
分支：`release/v0.1.0`

## 功能范围

- 用户认证：注册、登录、刷新令牌、会话恢复
- 文件中心：列表、筛选、分片上传、下载（Range）
- 文件预览：图片/PDF/TXT
- 回收站：软删除、恢复、彻底删除
- 操作日志：关键动作写入与管理员查询
- 管理端：文件管理页、日志页
- 管理员初始化：启动时可按环境变量自动创建/校正管理员

## 质量验证结果

- 后端测试：`APP_SERVE_FRONTEND=false pytest -q` 通过（44 passed）
- 主链路烟雾：`APP_SERVE_FRONTEND=false python scripts/smoke_core_flow.py` 通过
- 性能基线：`APP_SERVE_FRONTEND=false python scripts/perf_baseline.py`
  - `files_list_avg=1.78ms`
  - `files_download_avg=1.92ms`
  - `upload_complete_avg=16.60ms`
- 前端构建：`npm run build` 通过
- 前端常规 E2E：`npm run e2e` 通过（12 passed）
- 后端托管前端 smoke：`npm run e2e:hosted` 通过（1 passed）

## 已知风险

- 本地未连接 MinIO 时，下载与上传耗时偏高（重试回退路径）
- 前端 bundle 体积较大（>500kB），需后续拆包优化
- FastAPI `on_event` 与 `HTTP_416_*` 常量存在弃用告警，需后续治理

## 发布前确认

- 按 `docs/RELEASE_CHECKLIST.md` 完成逐项检查
- 若发布失败，按 `docs/ROLLBACK_PLAN.md` 执行回滚
- 说明：常规 E2E 与托管模式 E2E 需要顺序执行，不能并行占用 `127.0.0.1:8000`
