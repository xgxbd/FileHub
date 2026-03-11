# ROUND22 导航栏高度跳动根因分析

## 问题现象

- 在已登录状态下切换 `文件列表`、`上传`、`预览`、`后台日志` 等页面时，顶部下方那一行页面导航区域高度会明显变化。
- 用户感知为“那一栏在浮动”，底部横线位置不稳定。

## 可能原因

- `topbar` 或 `page-info` 高度不固定。
- 导航项激活态样式导致单个按钮尺寸变化。
- 页面切换后滚动条出现/消失触发整体重排。
- 导航栏父容器被布局系统拉伸，不同页面下分配到的剩余高度不同。

## 验证步骤

1. 检查 `frontend/src/App.vue` 中顶部结构，确认跳动区域对应的实际 DOM。
2. 检查 `frontend/src/styles/main.css` 中 `.topbar`、`.page-info`、`.sidebar`、`.shell` 的布局策略。
3. 使用真实浏览器逐页测量 `.topbar`、`.page-info`、`.sidebar` 的 `getBoundingClientRect().height`。
4. 对比 `文件列表`、`上传`、`预览`、`后台日志` 四页下导航按钮实际坐标与容器高度。

## 验证结果

- `.topbar` 在四个页面中始终是 `80px`，`.page-info` 始终是 `44px`，并未变化。
- 真正变化的是 `.sidebar`：
  - `/preview` 约 `56.75px`
  - `/upload` 约 `124px`
  - `/files` 约 `146px`
  - `/admin/logs` 约 `161.56px`
- 同时导航按钮自身高度始终约 `27px`，但其 `top` 坐标在不同页面中被整体向下推。
- 当前 `.shell` 使用 `display: grid` 且设置了 `min-height: calc(100vh - 80px)`，在多行自动轨道下，剩余高度会被拉伸分配。
- 当前 `.sidebar` 使用 `align-items: flex-end`，在被拉高后，按钮会被压到容器底部，视觉上形成“导航栏高度跳动”。

## 最终根因

- 根因不是标题文本高度变化，而是 **`.shell` 的 Grid 自动行在 `min-height` 条件下被拉伸**。
- 被拉伸后的 `.sidebar` 又通过 `align-items: flex-end` 把导航按钮贴到底部，导致该栏在不同页面看起来忽高忽低。

## 修复方案

1. 将 `.shell` 从 Grid 改为纵向 Flex 容器，避免自动行因剩余高度被拉伸。
2. 将 `.sidebar` 的垂直对齐从 `flex-end` 改为 `center`，保证导航按钮在固定高度内稳定排列。
3. 保留现有 `topbar`、`page-info` 固定高度，不再继续改标题容器。

## 验证标准

- 切换 `文件列表`、`上传`、`预览`、`后台日志` 四页时，`.sidebar` 高度保持一致。
- 导航按钮的 `top` 坐标保持一致，底部横线位置不再跳动。
