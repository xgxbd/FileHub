# FileHub

FileHub 是一个从零开始构建的 Web 文件仓库系统，目标是提供“上传-管理-下载-回收-审计”的完整闭环能力。

## 当前阶段

- 已建立 GitFlow 基线分支：`main`、`develop`、`feature/*`
- 正在推进 V0.1：先产品规划与 UI 设计，再技术设计与开发实现

## 技术栈

- 前端：Vue 3 + PrimeVue
- 后端：FastAPI
- 数据与存储：MySQL + Redis + MinIO

## 开发约束

- 仅允许在项目虚拟环境中运行 Python
- 每个最小可验证改动独立提交，提交信息为具体中文自然语言
- 每次任务完成都更新 `docs/PROGRESS.md`

