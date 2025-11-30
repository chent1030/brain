# 快速入门: AI对话系统

**功能**: AI对话系统
**更新日期**: 2025-11-24
**目标**: 5分钟内启动本地开发环境

## 前置要求

### 必需软件

| 软件 | 最低版本 | 安装验证 |
|------|---------|---------|
| Python | 3.11+ | `python3 --version` |
| Node.js | 18.x+ | `node --version` |
| PostgreSQL | 15+ | `psql --version` |
| Git | 2.30+ | `git --version` |

### 可选软件

- **Docker**: 用于容器化运行（推荐）
- **Postman/Insomnia**: API测试工具

---

## 快速启动（Docker方式）⚡

最快的方式启动完整系统（后端 + 前端 + 数据库）：

```bash
# 1. 克隆仓库
git clone <repo-url>
cd brain

# 2. 配置环境变量
cp .env.example .env
# 编辑.env文件，填写API密钥（见下文）

# 3. 启动所有服务
docker-compose up -d

# 4. 初始化数据库
docker-compose exec backend alembic upgrade head

# 5. 打开浏览器
open http://localhost:3000
```

**完成！** 🎉 前端运行在 http://localhost:3000，后端API在 http://localhost:8000

---

## 手动启动（本地开发）

### 步骤1: 数据库设置

```bash
# 创建数据库
createdb brain_dev

# 或使用psql
psql -U postgres
CREATE DATABASE brain_dev;
\q
```

### 步骤2: 后端设置

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 编辑.env文件（见下文"环境变量配置"）
nano .env

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn src.main:app --reload --port 8000
```

后端API现在运行在 **http://localhost:8000**

API文档: http://localhost:8000/docs (Swagger UI)

### 步骤3: 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local

# 启动开发服务器
npm run dev
```

前端应用现在运行在 **http://localhost:3000**

---

## 环境变量配置

### 后端环境变量 (`backend/.env`)

```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/brain_dev

# 会话密钥（生成方法: python -c "import secrets; print(secrets.token_hex(32))"）
SESSION_SECRET_KEY=your-secret-key-here

# 通义API配置
TONGYI_API_KEY=your-tongyi-api-key
TONGYI_API_BASE=https://dashscope.aliyuncs.com/api/v1

# MCP服务器配置
MCP_SERVER_URL=http://localhost:3001
MCP_SERVER_TIMEOUT=5

# Deep Research配置
DEEP_RESEARCH_TIMEOUT=30
DEEP_RESEARCH_MAX_TOKENS=4096

# 数据保留策略
DATA_RETENTION_DAYS=30

# 日志级别
LOG_LEVEL=INFO

# 开发模式
DEBUG=True
```

### 前端环境变量 (`frontend/.env.local`)

```bash
# API基础URL
VITE_API_BASE_URL=http://localhost:8000/api

# SSE端点
VITE_SSE_BASE_URL=http://localhost:8000/api

# 功能开关
VITE_ENABLE_CHART=true
VITE_ENABLE_HISTORY=true
```

---

## 获取API密钥

### 通义Deep Research API密钥

1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 创建应用并获取API Key
3. 将API Key填入 `TONGYI_API_KEY`

### MCP服务器设置

```bash
# 全局安装@antv/mcp-server-chart
npm install -g @antv/mcp-server-chart

# 启动MCP服务器（默认端口3001）
mcp-server-chart start

# 验证服务器运行
curl http://localhost:3001/health
```

---

## 验证安装

### 1. 检查后端健康

```bash
curl http://localhost:8000/health

# 预期输出
{"status": "healthy", "database": "connected", "mcp_server": "reachable"}
```

### 2. 检查API文档

访问 http://localhost:8000/docs 查看Swagger UI自动生成的API文档

### 3. 测试完整流程

```bash
# 创建会话
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "测试会话"}' \
  --cookie-jar cookies.txt

# 发送消息
curl -X POST http://localhost:8000/api/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "分析AI市场趋势"}' \
  --cookie cookies.txt

# 建立SSE连接（使用浏览器或Postman）
# GET http://localhost:8000/api/sessions/{session_id}/stream
```

### 4. 测试前端

1. 打开 http://localhost:3000
2. 输入问题："分析2024年AI市场"
3. 观察实时流式响应和图表渲染

---

## 数据库管理

### 查看数据库表

```bash
psql -U postgres -d brain_dev

-- 列出所有表
\dt

-- 查看会话
SELECT id, title, created_at, message_count FROM sessions;

-- 查看消息
SELECT id, role, content, created_at FROM messages LIMIT 10;
```

### 创建新迁移

```bash
cd backend

# 生成迁移文件
alembic revision --autogenerate -m "描述变更"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 重置数据库

```bash
# 删除所有表并重新创建
dropdb brain_dev
createdb brain_dev
alembic upgrade head
```

---

## 开发工作流

### 1. 拉取最新代码

```bash
git checkout 001-agent-conversation-system
git pull origin 001-agent-conversation-system
```

### 2. 安装新依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 3. 运行测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test
```

### 4. 代码格式化

```bash
# 后端格式化
cd backend
black src/
isort src/

# 前端格式化
cd frontend
npm run lint
npm run format
```

### 5. 提交变更

```bash
git add .
git commit -m "feat: 实现XXX功能"
git push origin 001-agent-conversation-system
```

---

## 常见问题

### Q: 数据库连接失败

**错误**: `could not connect to server: Connection refused`

**解决**:
```bash
# 检查PostgreSQL是否运行
pg_isready

# macOS启动PostgreSQL
brew services start postgresql@15

# Linux启动PostgreSQL
sudo systemctl start postgresql
```

### Q: MCP服务器无法访问

**错误**: `MCP server not reachable`

**解决**:
```bash
# 检查MCP服务器是否运行
curl http://localhost:3001/health

# 重新启动MCP服务器
mcp-server-chart start

# 检查端口占用
lsof -i :3001
```

### Q: 通义API返回401

**错误**: `Tongyi API authentication failed`

**解决**:
1. 检查 `TONGYI_API_KEY` 是否正确
2. 确认API Key有效期未过期
3. 检查阿里云账户余额

### Q: SSE连接立即断开

**错误**: EventSource连接失败

**解决**:
1. 检查会话cookie是否正确传递
2. 确认会话ID有效
3. 查看浏览器控制台网络面板的SSE请求详情

### Q: 前端图表无法渲染

**错误**: 图表显示为空白

**解决**:
1. 打开浏览器控制台查看错误
2. 检查`chart_config`格式是否符合AntV G2规范
3. 确认MCP服务器返回的图表类型是否支持

---

## 性能优化建议

### 开发环境

```bash
# 后端：启用热重载
uvicorn src.main:app --reload --log-level debug

# 前端：启用快速刷新
npm run dev

# 数据库：增加连接池
# backend/src/config.py
DATABASE_POOL_SIZE = 5
DATABASE_MAX_OVERFLOW = 10
```

### 生产环境

见 `docs/deployment.md`（后续创建）

---

## 下一步

- 📖 阅读 [数据模型文档](./data-model.md)
- 📋 查看 [API契约](./contracts/openapi.yaml)
- 🔄 了解 [SSE事件流](./contracts/asyncapi.yaml)
- 📝 查看 [实施任务列表](./tasks.md)（使用 `/speckit.tasks` 生成）

---

## 技术支持

- **问题追踪**: GitHub Issues
- **文档**: `specs/001-agent-conversation-system/`
- **章程**: `.specify/memory/constitution.md`

**祝开发顺利！** 🚀
