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
- 状态管理：Pinia `auth` store
- 会话恢复：应用启动自动执行 `initSession`

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
