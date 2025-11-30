# 仓库指南

## 项目结构与模块组织
- 后端（`backend/`）：FastAPI 应用位于 `backend/app/`，包含 `api/`、`core/`、`models/`、`schemas/`、`services/`，入口为 `app/main.py`。数据库迁移在 `backend/alembic/`。测试在 `backend/tests/`（`unit/`、`integration/`、`contract/`、`performance/`）。
- 前端（`frontend/`）：React + TypeScript 源码在 `frontend/src/`（`components/`、`views/`、`stores/`、`router/`、`api/`、`assets/`）。
- 编排：根目录 `docker-compose.yml`；环境示例在 `./.env.example`、`backend/.env.example`、`frontend/.env.example`。

## 构建、测试与开发命令
- 后端
  - 初始化：`cd backend && uv sync && cp .env.example .env`
  - 开发运行：`uv run fastapi dev app/main.py`
  - 数据迁移：`uv run alembic upgrade head`
  - 测试：`uv run pytest`（示例：`-m unit`、`--cov=app`）
- 前端
  - 初始化：`cd frontend && yarn install`
  - 开发服务器：`yarn dev`（http://localhost:3000）
  - 构建/预览：`yarn build` / `yarn preview`
  - Lint/格式化/类型检查：`yarn lint` / `yarn format` / `yarn type-check`
- Docker
  - 启动服务：`docker-compose up -d`
  - 查看日志：`docker-compose logs -f`

## 编码风格与命名约定
- Python（后端）
  - 工具：Black（88 列）、isort（profile=black）、Flake8（`backend/.flake8`）、MyPy（严格）。
  - 命名：文件/模块 `snake_case.py`；类 `CamelCase`；函数/变量 `snake_case`；常量 `UPPER_SNAKE`。
- TypeScript/Vue（前端）
  - 工具：ESLint（`frontend/eslint.config.js`）、Prettier（`.prettierrc`：2 空格、单引号、无分号）。
  - 命名：组件 `PascalCase.tsx`（如 `OrdersView.tsx`）、组合式 `useX.ts`、状态 `stores/*.ts`、接口 `api/*.ts`。

## 测试规范
- 后端：Pytest 标记（`unit`、`integration`、`contract`、`performance`）。测试放在 `backend/tests/`，文件名 `test_*.py`。子集运行：`uv run pytest -m "unit"`。默认收集覆盖率（`--cov=app`）。
- 前端：Vitest（`yarn test`、`yarn test:coverage`）。建议就近 `*.spec.ts` 或 `src/**/__tests__`。

## 提交与 Pull Request 规范
- 提交：语义清晰、现在时；中英文均可；按逻辑原子提交；需要时关联 Issue。示例：`fix(orders): prevent duplicate grab in race`。
- PR：包含目的、变更摘要、UI 截图、测试步骤、迁移/环境变更；链接相关 Issue，并请求评审。

## 安全与配置提示
- 请勿提交敏感信息。基于 `*.env.example` 创建 `.env`，保存 JWT/DB/Redis 配置。
- 启动 API 前先执行数据库迁移；启用队列/WebSocket 时确保 Redis/Postgres 可用。

## 回复语言
- 始终以**中文**回复

