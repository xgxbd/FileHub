# Round 34 测试与发布准备问题根因分析

## 问题一：全量 E2E 中 `core-flow.spec.js` 失败

- 问题现象：
  - 全量执行 `npm run e2e` 时，`核心流程：注册登录上传下载删除恢复` 用例失败。
  - 失败点是 `expect(getByText('上传完成')).toBeVisible()`。
- 可能原因：
  - 上传页面的成功反馈文案发生了重复，导致 Playwright 严格模式命中多个节点。
  - 上传逻辑实际失败，但页面出现了局部成功文案。
- 验证步骤：
  - 查看 `frontend/e2e/core-flow.spec.js` 的断言写法。
  - 查看 `frontend/src/views/UploadView.vue` 上传完成后页面上有哪些“上传完成”文本节点。
- 验证结果：
  - 上传成功后页面中同时存在：
    - `上传完成：文件名`
    - `上传完成`
  - E2E 断言使用了宽泛的文本定位，导致 strict mode 触发失败。
- 最终根因：
  - 这是测试断言过宽，不是业务链路失败。
- 修复方案：
  - 将断言改为更具体的成功消息或更稳定的状态节点，避免模糊文本匹配。

## 问题二：全量 E2E 中 `upload-preview-flow.spec.js` 上传后预览返回 404

- 问题现象：
  - 单独执行部分预览链路时可以通过。
  - 在全量 E2E 中，`/api/files/{id}/preview` 偶发返回 `404`。
- 可能原因：
  - 上传后对象内容没有成功落盘。
  - 测试读取的不是本次刚上传的文件，而是目录下的历史脏数据。
  - 预览接口本身存在权限或对象路径回退问题。
- 验证步骤：
  - 查看 `frontend/e2e/upload-preview-flow.spec.js` 取文件 ID 的方式。
  - 检查 E2E 使用的数据库是否会跨用例复用。
  - 对照后端预览相关测试与上传逻辑。
- 验证结果：
  - 当前测试通过 `/api/files?directory=logs` 后直接取 `items[0]` 进行预览。
  - E2E 后端使用固定数据库 `e2e_suite.db`，多次运行后会积累旧数据。
  - 当目录下存在历史文件或孤儿数据时，`items[0]` 不一定是本次刚上传的文件。
- 最终根因：
  - 这是测试数据隔离不足与定位方式不精确导致的失败，不是当前上传后预览主链路新增回归。
- 修复方案：
  - 为测试文件名加唯一后缀。
  - 列表查询时按唯一文件名过滤，确保命中当前测试数据。
  - 补充“后端托管前端”模式的独立浏览器级 smoke，用于发布前验证真实交付链路。

## 本轮执行顺序

1. 修复上述两个 E2E 用例。
2. 新增后端托管前端模式的 Playwright 验证配置。
3. 执行：
   - `cd backend && source .venv/bin/activate && APP_SERVE_FRONTEND=false pytest -q`
   - `cd frontend && npm run e2e`
   - `cd frontend && npm run e2e:hosted`
4. 再更新发布与回滚文档。
