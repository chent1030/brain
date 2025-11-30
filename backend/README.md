# Backend - Brain AI 对话系统

FastAPI 后端服务,提供 AI 对话、图表生成和历史记录管理功能。

## 技术栈

- Python 3.11+
- FastAPI (Web 框架)
- PostgreSQL 15+ (数据库)
- SQLAlchemy 2.0 (异步 ORM)
- Alembic (数据库迁移)
- DashScope SDK (通义 API)

## 快速开始

### 1. 安装 uv

首先安装 uv（如果还没有安装）：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip
pip install uv
```

### 2. 安装依赖

使用 uv 安装项目依赖（推荐）：

```bash
# 同步所有依赖（生产 + 开发）
uv sync

# 仅安装生产依赖
uv sync --no-dev

# 添加新依赖
uv add <package-name>

# 添加开发依赖
uv add --dev <package-name>
```

或使用传统方式：

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件,设置必需的配置项
```

### 4. 初始化数据库

```bash
# 运行迁移
alembic upgrade head
```

### 5. 启动服务

使用 uv 运行（推荐）：

```bash
# 开发模式（自动重载）
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

或直接运行：

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档。

## 使用 Makefile (推荐)

项目提供了 Makefile 来简化常用命令：

```bash
# 查看所有可用命令
make help

# 安装依赖
make install

# 启动开发服务器
make dev

# 运行测试
make test

# 格式化代码
make format

# 运行数据库迁移
make migrate

# 创建新迁移
make migrate-create MSG="add new field"

# 添加依赖
make add PKG=httpx

# 添加开发依赖
make add-dev PKG=pytest-mock
```

## 项目结构

```
backend/
├── src/
│   ├── api/              # API 路由
│   │   ├── health.py     # 健康检查
│   │   ├── sessions.py   # 会话管理
│   │   ├── messages.py   # 消息管理
│   │   ├── stream.py     # SSE 流式传输
│   │   └── error_handlers.py  # 错误处理
│   ├── config/           # 配置
│   │   ├── database.py   # 数据库连接
│   │   ├── settings.py   # 应用配置
│   │   ├── session.py    # 会话中间件
│   │   └── logging.py    # 日志配置
│   ├── models/           # 数据模型
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── message.py
│   │   └── chart.py
│   ├── services/         # 业务逻辑
│   │   ├── deep_research_client.py  # 通义客户端
│   │   ├── mcp_client.py            # MCP 客户端
│   │   ├── session_service.py       # 会话服务
│   │   ├── message_service.py       # 消息服务
│   │   ├── conversation_service.py  # 对话服务
│   │   └── sse_service.py          # SSE 服务
│   ├── utils/            # 工具函数
│   │   └── auth.py       # 认证工具
│   └── main.py           # 应用入口
├── alembic/              # 数据库迁移
├── requirements.txt      # Python 依赖
└── .env.example         # 环境变量模板
```

## API 端点

### 健康检查
- `GET /api/health` - 基础健康检查
- `GET /api/health/ready` - 就绪检查(包含数据库)
- `GET /api/health/live` - 存活检查

### 会话管理
- `POST /api/sessions` - 创建会话
- `GET /api/sessions` - 获取会话列表(分页)
- `GET /api/sessions/{id}` - 获取会话详情
- `PATCH /api/sessions/{id}` - 更新会话标题
- `DELETE /api/sessions/{id}` - 删除会话(软删除)

### 消息管理
- `POST /api/sessions/{id}/messages` - 发送用户消息
- `GET /api/sessions/{id}/messages` - 获取消息历史
- `GET /api/messages/{id}` - 获取单条消息

### 流式传输
- `GET /api/sessions/{id}/stream?query=xxx` - SSE 流式传输 AI 响应

## 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述"

# 升级数据库
alembic upgrade head

# 降级数据库
alembic downgrade -1

# 查看历史
alembic history

# 查看当前版本
alembic current
```

## 测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_api.py

# 查看覆盖率
pytest --cov=src tests/
```

## 开发指南

### 添加新的 API 端点

1. 在 `src/api/` 创建新的路由文件
2. 在 `src/main.py` 注册路由
3. 如需数据库操作,在 `src/services/` 创建服务类

### 添加新的数据模型

1. 在 `src/models/` 创建模型文件
2. 运行 `alembic revision --autogenerate -m "描述"`
3. 检查生成的迁移文件
4. 运行 `alembic upgrade head`

## 配置说明

所有配置通过环境变量管理,参见 `.env.example`。

关键配置项:
- `DATABASE_URL` - PostgreSQL 连接字符串
- `TONGYI_API_KEY` - 通义 API 密钥(必需)
- `SESSION_SECRET_KEY` - 会话加密密钥(生产环境必需)
- `MCP_SERVER_URL` - MCP 服务器地址(可选)

## 故障排除

### 数据库连接失败
- 检查 PostgreSQL 是否运行
- 验证 `DATABASE_URL` 格式正确
- 确认数据库已创建

### 通义 API 调用失败
- 验证 `TONGYI_API_KEY` 是否有效
- 检查网络连接
- 查看日志了解详细错误信息
