# FileHub 回滚预案（MVP）

## 1. 触发条件

- 发布后核心链路失败（登录、上传、下载、回收、日志查询）
- 服务不可用持续超过 5 分钟
- 数据写入错误或权限异常导致高风险影响

## 2. 回滚策略

1. 代码回滚：
   - 将部署版本回退到上一个稳定 tag 或 commit
2. 配置回滚：
   - 回退 `.env` 与基础服务配置到发布前快照
3. 服务重启：
   - 按顺序重启后端与前端服务

## 3. 数据与存储处理

- 数据库：
  - 本项目当前以 `create_all` 为主，发布前需备份数据库
  - 若出现元数据异常，优先恢复备份
- 对象存储：
  - MinIO 对象以追加为主，回滚代码不直接删除对象
  - 如需清理异常对象，应按对象 key 白名单执行

## 4. 回滚后验证清单

- `GET /healthz` 正常返回
- 登录/上传/下载/回收链路可用
- 管理员页面 `/admin/files`、`/admin/logs` 可访问
- `python scripts/smoke_core_flow.py` 执行通过
- `cd frontend && npm run e2e:hosted` 至少通过托管模式 smoke 验证

## 5. 记录要求

- 记录回滚时间、触发原因、影响范围、恢复时间
- 在 `docs/PROGRESS.md` 追加回滚事件条目

## 6. 最小回滚执行模板

```bash
# 1. 切回上一个稳定版本
git checkout <stable-tag-or-commit>

# 2. 恢复环境配置
cp <release-backup-env> backend/.env

# 3. 重启后端
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 4. 托管模式验收
cd ../frontend
npm run e2e:hosted
```
