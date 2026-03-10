# Round 8 回收站 MVP 设计

## 1. 目标

- 实现文件“软删除 -> 回收站查看 -> 恢复/彻底删除”闭环。

## 2. 范围

- 后端：
  - 软删除：`DELETE /files/{file_id}`
  - 回收站列表：`GET /recycle/files`
  - 恢复：`POST /recycle/files/{file_id}/restore`
  - 彻底删除：`DELETE /recycle/files/{file_id}/purge`
- 前端：
  - 文件中心增加“删除”操作
  - 新增回收站页面（列表 + 恢复 + 彻底删除）

## 3. 数据策略

- 复用 `file_objects.is_deleted` 与 `status` 字段
- 软删除：`is_deleted=true`、`status=deleted`
- 恢复：`is_deleted=false`、`status=active`
- 彻底删除：删除数据库记录，并尝试删除对象存储文件

## 4. 权限策略

- 普通用户仅操作自己的文件
- 管理员可操作全部文件

## 5. 最小提交拆分

### 提交 A（设计）
- 文档 + 进度记录
- 验证：文档可评审

### 提交 B（后端回收站接口）
- 软删/列表/恢复/彻删接口
- 验证：脚本完成删除->恢复->彻删链路

### 提交 C（后端测试）
- 覆盖权限与状态流转
- 验证：`pytest -q` 通过

### 提交 D（前端回收站页面）
- 页面与操作按钮接入
- 验证：`npm run build` 通过

### 提交 E（文档收口）
- 更新 README 与进度文档
- 验证：按文档可联调回收站流程
