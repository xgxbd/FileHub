# FileHub UI 定版说明（方案 D）

## 1. 最终选型
- 最终 UI 基线：`V5 / Scheme D（极简留白风）`
- 选定原型入口：`docs/ui-prototypes/v5/scheme-d/preview.html`
- 参考预览图：`docs/ui-previews/v5/v5-d-files.png`

## 2. 页面集（必须保持）
- 登录页：`/login`
- 文件列表页：`/files`
- 上传页：`/upload`
- 预览页：`/preview/:fileId?`
- 回收站页：`/recycle`
- 后台管理页：`/admin/files`
- 操作日志页：`/admin/logs`

## 3. 视觉令牌
- 背景：`#FAFAFA`
- 面板：`#FFFFFF`
- 分割线：`#E8E8E8`
- 主文本：`#111111`
- 次级文本：`#6A6A6A`
- 成功：`#166534`
- 警告：`#9A3412`
- 危险：`#991B1B`

## 4. 排版与布局
- 标题字体：`Iowan Old Style / Songti SC`
- 正文字体：`Helvetica Neue / PingFang SC`
- 固定结构：`Topbar(78px) + Shell(max-width:1040) + Sidebar + KPI + Content`
- 页面密度：中低密度，弱色块、强线条、留白优先

## 5. 组件约束
- 数据表格、筛选栏、详情区使用单层面板结构，不做卡片瀑布化
- 上传和预览必须是独立页面，不允许回退为列表页内嵌弹层
- 导航与页面标题统一由全局壳层提供，页面组件只负责业务内容

## 6. 开发约束（后续所有改动）
- 所有新增页面与改动必须遵守本方案 D 令牌与布局结构
- 如果功能需要新增组件，先在本文件补充样式约束后再实现
- 禁止引入与方案 D 冲突的高饱和配色和重阴影风格

## 7. 验收参考
- 原型比对：`docs/ui-prototypes/v5/scheme-d/*.html`
- 运行比对：前端路由页面与方案 D 在信息架构、版式层级、主视觉方向一致
