# Brain AI 对话系统

基于通义 Deep Research 和 MCP 图表服务的 AI 对话系统,支持流式对话、图表生成和历史记录管理。

## 功能特性

- **实时AI对话**: 使用通义千问(Qwen)进行深度研究和对话
- **图表生成**: 通过 @antv/mcp-server-chart 自动生成数据可视化图表
- **流式响应**: 使用 Server-Sent Events (SSE) 实时流式返回 AI 响应
- **历史记录**: 完整的对话历史存储和检索
- **响应式界面**: 现代化的 React 界面,支持实时更新

## 技术栈

### 后端
- **Python 3.11+** - 编程语言
- **FastAPI** - Web 框架
- **PostgreSQL 15+** - 数据库
- **SQLAlchemy 2.0** - 异步 ORM
- **DashScope SDK** - 通义 API 集成
- **Alembic** - 数据库迁移

### 前端
- **TypeScript 5.x** - 类型安全的 JavaScript
- **React 18+** - UI 框架
- **Vite 5.x** - 构建工具
- **AntV G2** - 图表渲染库

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- 通义 API 密钥 ([申请地址](https://dashscope.aliyuncs.com/))
- @antv/mcp-server-chart 服务(可选,用于图表生成)

### 使用 Docker Compose (推荐)

1. **克隆仓库**
```bash
git clone <repository-url>
cd brain
```

2. **配置环境变量**
```bash
# 复制环境变量模板
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 编辑 backend/.env,设置必需的配置
# TONGYI_API_KEY=your-api-key-here
```

3. **启动所有服务**
```bash
docker-compose up -d
```

4. **访问应用**
- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 本地开发

#### 安装 uv（推荐）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 后端开发（使用 uv）

```bash
cd backend

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 运行数据库迁移
uv run alembic upgrade head

# 启动开发服务器
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

<details>
<summary>或使用传统方式（pip + venv）</summary>

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
</details>

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动开发服务器
npm run dev
```

## 环境变量说明

### 后端 (backend/.env)

```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/brain_dev

# 会话密钥(生产环境必须修改)
SESSION_SECRET_KEY=your-secret-key-here

# 通义 API 配置
TONGYI_API_KEY=your-tongyi-api-key-here
TONGYI_API_BASE=https://dashscope.aliyuncs.com/api/v1

# MCP 服务器配置
MCP_SERVER_URL=http://localhost:3001
MCP_SERVER_TIMEOUT=5

# Deep Research 配置
DEEP_RESEARCH_TIMEOUT=30
DEEP_RESEARCH_MAX_TOKENS=4096

# 数据保留策略(天数)
DATA_RETENTION_DAYS=30

# 日志级别
LOG_LEVEL=INFO

# 开发模式
DEBUG=True

# CORS 配置
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 前端 (frontend/.env)

```bash
# API 基础 URL
VITE_API_BASE_URL=http://localhost:8000/api

# SSE 端点基础 URL
VITE_SSE_BASE_URL=http://localhost:8000/api

# 功能开关
VITE_ENABLE_CHART=true
VITE_ENABLE_HISTORY=true

# 调试模式
VITE_DEBUG=false
```

## API 文档

启动后端服务后,访问以下地址查看 API 文档:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
brain/
├── backend/               # 后端服务
│   ├── src/
│   │   ├── api/          # API 端点
│   │   ├── config/       # 配置管理
│   │   ├── models/       # 数据模型
│   │   ├── services/     # 业务逻辑
│   │   └── utils/        # 工具函数
│   ├── alembic/          # 数据库迁移
│   └── requirements.txt  # Python 依赖
├── frontend/             # 前端应用
│   ├── src/
│   │   ├── components/   # React 组件
│   │   ├── hooks/        # React Hooks
│   │   ├── services/     # API 客户端
│   │   └── types/        # TypeScript 类型
│   └── package.json      # Node.js 依赖
├── docker-compose.yml    # Docker Compose 配置
└── README.md            # 本文件
```

## 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述"

# 升级到最新版本
alembic upgrade head

# 降级一个版本
alembic downgrade -1

# 查看当前版本
alembic current
```

## 测试

### 后端测试
```bash
cd backend
pytest
```

### 前端测试
```bash
cd frontend
npm test
```

## 生产部署

1. **设置环境变量**
   - 修改 `backend/.env` 中的 `SESSION_SECRET_KEY`
   - 设置 `ENV=production`
   - 设置 `DEBUG=False`

2. **使用生产数据库**
   - 配置 PostgreSQL 生产实例
   - 运行数据库迁移

3. **构建和部署**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 常见问题

### Q: 如何获取通义 API 密钥?
A: 访问 [阿里云DashScope](https://dashscope.aliyuncs.com/) 注册并申请 API 密钥。

### Q: MCP 服务器是必需的吗?
A: 不是必需的。如果不配置 MCP 服务器,系统仍可正常进行对话,只是不会生成图表。

### Q: 数据会保留多久?
A: 默认 30 天自动软删除,可通过 `DATA_RETENTION_DAYS` 环境变量配置。

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request!
