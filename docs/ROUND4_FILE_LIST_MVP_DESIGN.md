# Round 4 文件列表 MVP 设计（先设计后实现）

## 1. 目标

- 打通“已登录用户 -> 查看自己的文件列表 -> 基础筛选查询”的闭环。
- 聚焦元数据查询，不实现上传、下载、预览主体链路。

## 2. 范围

- 后端：
  - 文件元数据模型 `file_objects`
  - 列表接口 `GET /files`
  - 基础筛选：关键字（文件名）、大小区间、分页
  - 权限：普通用户仅看自己的文件；管理员可看全部
- 前端：
  - 文件中心页接入列表接口
  - 筛选控件（关键字/最小大小/最大大小）
  - 分页与加载状态

## 3. 接口定义

### `GET /files`

Query：
- `keyword`（可选）
- `min_size`（可选，单位字节）
- `max_size`（可选，单位字节）
- `page`（默认 1）
- `page_size`（默认 20，最大 100）

Response：
- `items`: 文件列表
- `total`: 总数
- `page`: 当前页
- `page_size`: 每页条数

## 4. 数据模型（MVP）

`file_objects`：
- `id` int PK
- `owner_id` int FK(users.id)
- `file_name` varchar(255)
- `object_key` varchar(512)
- `size_bytes` bigint
- `mime_type` varchar(128)
- `status` varchar(16) default `active`
- `is_deleted` bool default false
- `created_at` / `updated_at`

## 5. 最小提交拆分

### 提交 A（设计）
- 内容：本设计文档 + 进度记录。
- 验证：文档可评审。

### 提交 B（后端列表能力）
- 内容：文件模型、schema、服务、`GET /files` 接口接入。
- 验证：后端脚本验证登录后调用 `/files` 返回 200。

### 提交 C（后端测试）
- 内容：新增文件列表接口测试（鉴权、筛选、分页）。
- 验证：`pytest -q` 通过。

### 提交 D（前端页面接入）
- 内容：文件中心页接入接口、筛选表单、表格与分页。
- 验证：`npm run build` 通过。

### 提交 E（文档收口）
- 内容：更新前后端 README 与进度文档。
- 验证：按文档可执行构建/测试命令。
