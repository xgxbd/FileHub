# frontend

前端工程目录（Vue 3 + PrimeVue）。

当前阶段已完成最小可运行骨架（Vue Router + PrimeVue 主题加载）。

## 本地运行（MVP 骨架）

```bash
npm install
npm run dev
```

默认通过 Vite 代理将 `/api/*` 转发到 `http://127.0.0.1:8000/*`，用于本地联调后端接口。

## 认证接入（第三轮）

- 路由：
  - `/login` 登录
  - `/register` 注册
  - `/files` 文件中心（需登录）
  - `/recycle` 回收站（需登录）
  - `/admin/files` 管理端文件管理页（需管理员）
  - `/admin/logs` 操作日志页（需管理员）
- 状态管理：Pinia `auth` store
- 会话恢复：应用启动自动执行 `initSession`

## 文件列表接入（第四轮）

- 文件中心页面：`/files`
- 已接入后端 `GET /files`
- 支持筛选：文件名关键字、最小大小、最大大小
- 支持分页浏览
- 列表操作：下载按钮（对接后端 Range 下载接口）
- 列表操作：预览按钮（支持图片/PDF/TXT）

## 分片上传接入（第五轮）

- 文件中心页面新增上传面板
- 上传流程：创建会话 -> 分片上传 -> 完成合并
- 上传完成后自动刷新文件列表

## 回收站接入（第八轮）

- 文件中心列表新增“删除”按钮（软删除）
- 回收站页面支持恢复与彻底删除
- 顶部导航已提供回收站入口

## 操作日志接入（第九轮）

- 新增管理员日志页 `/admin/logs`
- 支持按操作类型、用户ID、时间范围筛选
- 仅管理员可访问，普通用户自动回退至 `/files`

## 管理端文件管理接入（第十一轮）

- 新增管理员文件管理页 `/admin/files`
- 支持按 owner、关键字、状态筛选文件
- 支持删除、恢复、彻底删除状态操作

## 前端关键流程 E2E（第十三轮）

- 用例目录：`frontend/e2e/`
- 查看用例：
  ```bash
  cd frontend
  npm run e2e:list
  ```
- 执行一次：
  ```bash
  cd frontend
  npm run e2e
  ```
- 连续两次稳定性回归：
  ```bash
  cd frontend
  npm run e2e:repeat
  ```

## 联调验证

1. 启动后端：
   ```bash
   cd backend
   source .venv/bin/activate
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. 启动前端：
   ```bash
   cd frontend
   npm run dev
   ```
3. 浏览器验证：
   - 未登录访问 `/files` 会跳转 `/login`
   - 注册成功后自动进入 `/files`
   - 登录后刷新页面仍保持登录态（token 有效时）
