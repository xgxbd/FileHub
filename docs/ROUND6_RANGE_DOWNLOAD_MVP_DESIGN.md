# Round 6 下载断点续传（Range）MVP 设计

## 1. 目标

- 实现文件下载接口的 HTTP Range 支持，满足断点续传能力。
- 前端文件中心接入下载动作，使用后端鉴权下载接口。

## 2. 范围

- 后端：
  - `GET /files/{file_id}/download`
  - 支持 `Range: bytes=start-end` 请求头
  - 返回 `206 Partial Content` 与 `Content-Range`、`Accept-Ranges`
  - 权限：普通用户仅下载自己的文件，管理员可下载全部
- 前端：
  - 文件中心列表增加下载按钮
  - 调用下载接口并触发浏览器保存

## 3. 响应约束

- 全量下载：`200 OK`
- 分段下载：`206 Partial Content`
- 非法 Range：`416 Requested Range Not Satisfiable`
- 关键响应头：
  - `Accept-Ranges: bytes`
  - `Content-Range: bytes start-end/total`（206）
  - `Content-Length`

## 4. 对象存储读取策略

- 优先 MinIO 读取对象
- MinIO 不可用时回落本地对象目录（开发测试）
- 接口层统一由 `object_storage_service` 提供读取与对象大小

## 5. 最小提交拆分

### 提交 A（设计）
- 本文档 + 进度记录
- 验证：文档可评审

### 提交 B（后端 Range 下载能力）
- 新增下载接口与 Range 解析
- 扩展对象存储服务读取能力
- 验证：脚本上传后可下载，Range 请求返回 206

### 提交 C（后端测试）
- 新增下载接口测试：鉴权、全量、Range、越界
- 验证：`pytest -q` 通过

### 提交 D（前端下载接入）
- 文件中心新增下载按钮并接入接口
- 验证：`npm run build` 通过

### 提交 E（文档收口）
- 更新前后端 README 与进度文档
- 验证：按文档可执行下载联调
