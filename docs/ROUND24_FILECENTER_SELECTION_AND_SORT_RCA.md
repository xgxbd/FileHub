# ROUND24 文件列表页目录选择与排序问题根因分析

## 问题现象

- 点击左侧文件树中的目录后，列表内容没有按目录切换。
- 顶部“当前目录”标签没有同步到所点击目录。
- 切换排序方式后，文件列表没有立即重排。

## 可能原因

- PrimeVue `Tree` 的选中状态绑定类型错误，导致目录点击没有稳定进入“选中目录”流程。
- 文件树缺少显式展开状态控制，新目录在刷新后可能仍隐藏在根节点下。
- 排序控件仅修改本地状态，没有触发新的 `/files` 请求。

## 验证步骤

1. 检查 `frontend/src/views/FileCenterView.vue` 中 `Tree` 的 `selectionKeys` 和目录选择逻辑。
2. 检查 PrimeVue `Tree` 源码/类型定义，确认 `selectionKeys`、`expandedKeys` 的数据结构。
3. 在真实页面中创建根目录文件与 `logs/*` 文件，观察目录点击和排序切换后的实际表现。

## 验证结果

- 当前实现将 `v-model:selectionKeys` 绑定为字符串：
  - `const selectedTreeKey = ref(\`dir:${ROOT_DIRECTORY_MARKER}\`)`
- PrimeVue `Tree` 实际要求：
  - `selectionKeys` 为对象映射，如 `{ 'dir:logs': true }`
  - `expandedKeys` 为对象映射，如 `{ 'dir:__root__': true }`
- 当前未显式维护 `expandedKeys`，导致根节点下新增目录在刷新后仍依赖组件内部状态，不稳定。
- 当前排序方式 `sortBy` 仅在点击“查询”时才会重新请求；用户直接切换排序，不会自动重载列表。

## 最终根因

- 目录选择问题根因是 `Tree` 的受控状态绑定错误：
  - `selectionKeys` 用了错误的数据类型
  - `expandedKeys` 未显式控制
- 排序问题根因是排序值变化后没有自动触发 `loadFiles()`。

## 修复方案

1. 将 `selectionKeys` 改为对象映射。
2. 新增 `expandedKeys`，默认展开根目录，并在树刷新后保持根目录展开。
3. 目录切换时同步更新：
  - `selectedDirectory`
  - `selectionKeys`
  - 顶部“当前目录”标签
4. 监听 `sortBy` 变化并自动重新加载列表。

## 验证标准

- 点击 `logs` 后：
  - 顶部显示 `当前目录：logs`
  - 列表只显示 `logs` 目录直系文件
- 切回根目录后：
  - 顶部显示 `当前目录：根目录 /`
  - 列表只显示根目录直系文件
- 切换排序方式后，列表顺序立即变化，无需额外点击“查询”
