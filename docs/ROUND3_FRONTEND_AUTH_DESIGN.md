# Round 3 前端认证接入设计（先设计后实现）

## 1. 目标与范围

- 目标：完成前端登录/注册/会话管理最小闭环，并联通第二轮后端认证接口。
- 范围：
  - 登录页（`/login`）
  - 注册页（`/register`）
  - 文件中心占位页（`/files`，需登录访问）
  - 会话状态恢复、路由守卫、退出登录
- 非目标：
  - 忘记密码、验证码、短信登录
  - 多端会话管理
  - 完整 UI 方案 D 细节还原（本轮先功能闭环）

## 2. 前端模块设计

- `src/api/auth.js`
  - `register(payload)`
  - `login(payload)`
  - `refresh(payload)`
  - `fetchCurrentUser(token)`
- `src/stores/auth.js`
  - 状态：`accessToken`、`refreshToken`、`user`、`loading`
  - 动作：`initSession`、`login`、`register`、`loadProfile`、`logout`
- `src/utils/token.js`
  - 本地持久化：`localStorage` 中读写 token
- `src/router/index.js`
  - 路由元信息：`meta.requiresAuth`、`meta.guestOnly`
  - 全局守卫：未登录跳转 `/login`，已登录访问游客页重定向 `/files`
- 页面：
  - `views/LoginView.vue`
  - `views/RegisterView.vue`
  - `views/FileCenterView.vue`

## 3. 交互流程

1. 访问 `/files`：
   - 未登录 -> 跳转 `/login?redirect=/files`
2. 登录成功：
   - 保存 token -> 拉取 `/auth/me` -> 跳转 redirect 或 `/files`
3. 注册成功：
   - 自动执行登录流程并进入 `/files`
4. 刷新页面：
   - 启动时从本地恢复 token，尝试拉取 `/auth/me`
5. 退出登录：
   - 清空本地会话 -> 跳转 `/login`

## 4. 错误处理策略

- API 非 2xx：统一抛出错误消息给页面层。
- `/auth/me` 401：清空会话并回到登录页。
- 表单校验：前端最小校验（邮箱格式、密码长度 >= 8）。

## 5. 最小提交拆分（实现阶段）

### 提交 B：认证状态基础设施
- 内容：引入 Pinia、token 工具、auth API 封装、auth store（不改页面）。
- 验证：`npm run build` 成功；可通过脚本导入 store。

### 提交 C：登录/注册页面与路由守卫
- 内容：新增登录页、注册页、文件中心占位页；路由守卫接入。
- 验证：`npm run build` 成功；路由配置包含 `/login` `/register` `/files`。

### 提交 D：应用壳联动与会话恢复
- 内容：`App.vue` 增加登录态信息与退出；`main.js` 启动会话恢复。
- 验证：`npm run build` 成功；`initSession` 在启动时调用。

### 提交 E：文档与收尾测试
- 内容：更新前端 README 与进度文档，补充联调命令。
- 验证：`npm run build` 成功；文档可直接执行。
