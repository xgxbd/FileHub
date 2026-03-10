# 项目基础目录（第一轮）

## frontend

- `src/api/`：前端接口调用封装
- `src/assets/`：静态资源
- `src/components/`：通用组件
- `src/router/`：路由定义
- `src/stores/`：Pinia 状态模块
- `src/styles/`：全局样式与主题变量
- `src/views/`：页面级视图

## backend

- `app/api/`：FastAPI 路由层
- `app/core/`：配置、鉴权、中间件
- `app/models/`：ORM 模型
- `app/repositories/`：数据访问层
- `app/schemas/`：请求响应模型
- `app/services/`：业务服务层
- `app/utils/`：通用工具
- `tests/`：后端测试目录

## infra

- `docker-compose.yml`：本地基础依赖服务
- `.env.example`：基础服务环境变量样板

## docs

- `PROGRESS.md`：开发进度记录
- `PRD.md`：产品需求文档
- `TASKS.md`：任务拆分
- `IA_USER_FLOW.md`：页面信息架构与流程

