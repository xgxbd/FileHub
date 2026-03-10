# Round 5 分片上传 MVP 设计（先设计后实现）

## 1. 目标

- 打通大文件分片上传最小闭环：创建上传会话 -> 分片上传 -> 断点续传查询 -> 合并完成。
- 上传完成后写入 `file_objects` 元数据，文件内容写入 MinIO。

## 2. 范围

- 后端：
  - 上传会话接口（Redis 保存状态）
  - 分片上传接口（按 chunk index 上传）
  - 会话状态查询接口（返回已上传分片）
  - 合并完成接口（按顺序合并并上传 MinIO）
- 前端：
  - 文件中心增加上传面板（选择文件、自动切片上传、进度展示）
  - 失败重试与续传（基于会话状态）

## 3. 接口定义（MVP）

- `POST /upload/sessions`
  - 入参：`file_name`、`total_size`、`chunk_size`、`total_chunks`、`mime_type`、`file_hash?`
  - 出参：`upload_id`、`uploaded_chunks`、`chunk_size`
- `GET /upload/sessions/{upload_id}`
  - 出参：`status`、`uploaded_chunks`
- `PUT /upload/sessions/{upload_id}/chunks/{chunk_index}`
  - Body：`multipart/form-data`（`chunk`）
  - 出参：`chunk_index`、`uploaded_count`
- `POST /upload/sessions/{upload_id}/complete`
  - 出参：`file_id`、`file_name`、`size_bytes`、`object_key`

## 4. 状态存储

- Redis Key：`upload:session:{upload_id}`
- 字段：
  - `owner_id`、`file_name`、`total_size`、`chunk_size`、`total_chunks`
  - `uploaded_chunks`（整数数组）
  - `mime_type`、`file_hash`、`status`（uploading/completed）
- TTL：24h（MVP）

## 5. MinIO 写入策略

- 分片临时文件先落本地临时目录：`UPLOAD_TMP_DIR/{upload_id}/{chunk_index}.part`
- 完成时按 `0..total_chunks-1` 顺序合并成单文件，再上传 MinIO `object_key`
- 上传成功后写入 `file_objects` 元数据（owner/file_name/object_key/size/mime/status）

## 6. 最小提交拆分

### 提交 A（设计）
- 本文档 + 进度记录
- 验证：文档可评审

### 提交 B（后端上传会话）
- 配置扩展、Redis 上传会话仓库、创建/查询会话接口
- 验证：脚本可创建会话并查询状态

### 提交 C（后端分片接收与合并）
- 分片上传、完成合并、MinIO 写入、文件元数据入库
- 验证：脚本上传小文件分片后完成，`file_objects` 新增记录

### 提交 D（后端测试）
- 上传会话/分片/完成链路测试
- 验证：`pytest -q` 通过

### 提交 E（前端上传面板接入）
- 文件中心增加上传控件与分片上传逻辑
- 验证：`npm run build` 通过，联调可上传

### 提交 F（文档与收口）
- 更新前后端 README 与进度记录
- 验证：按文档可执行基本联调
