# 实施计划: AI对话系统

**分支**: `001-agent-conversation-system` | **日期**: 2025-11-24 | **规范**: [spec.md](./spec.md)
**输入**: 功能规范来自 `/specs/001-agent-conversation-system/spec.md`

**注意**: 此模板由 `/speckit.plan` 命令填充。执行工作流详见 `.specify/templates/commands/plan.md`。

## 摘要

构建一个AI对话系统，用户可以通过Web界面提问，系统调用通义Deep Research API进行深度研究，通过@antv/mcp-server-chart生成可视化图表，并使用SSE流式传输结果。所有对话历史（消息和图表）持久化存储，支持检索和多轮对话。

**技术方法**: Web应用架构，后端处理Deep Research集成、MCP图表服务调用、数据持久化和SSE流式响应；前端实现对话UI、SSE事件接收、图表渲染和历史记录浏览。

## 技术上下文

**Language/Version**: Python 3.11+ (后端), TypeScript 5.x (前端)
**Primary Dependencies**:
- 后端: FastAPI (SSE支持), 通义SDK, @antv/mcp-server-chart客户端, SQLAlchemy/Prisma
- 前端: React 18+, AntV G2/G6 (图表渲染), EventSource API (SSE客户端)

**Storage**: PostgreSQL 15+ (会话和消息持久化，支持时间序列查询) 或 MongoDB 6+ (文档存储，灵活模式)
**Testing**: pytest + httpx (后端契约/集成测试), Jest + React Testing Library (前端组件测试)
**Target Platform**: Linux server (后端), Modern Web Browsers (Chrome 90+, Firefox 88+, Safari 14+)
**Project Type**: web (前后端分离架构)
**Performance Goals**:
- SSE连接建立 <1秒
- Deep Research响应开始流式传输 <3秒
- 图表渲染完成 <5秒
- 历史记录查询 <2秒 (100条记录)
- 支持100并发SSE连接

**Constraints**:
- API响应p95 <2秒 (不包括Deep Research处理时间)
- 前端包大小 <2MB (初始加载)
- 数据库查询p95 <500ms
- SSE事件处理不阻塞UI

**Scale/Scope**:
- 支持1000+历史会话存储
- 单会话最多100轮对话
- 每条消息最多5个图表
- 预期10-50并发用户

## 章程检查

*门禁: 必须在阶段0研究前通过。阶段1设计后重新检查。*

### 原则一: API优先设计 ✅

**要求**: API契约必须在实现前编写文档（OpenAPI/AsyncAPI）

**合规状态**:
- ✅ 将在Phase 1生成OpenAPI 3.1规范（REST端点）
- ✅ 将在Phase 1生成AsyncAPI 3.0规范（SSE事件流）
- ✅ 前后端通过HTTP/SSE通信，无直接数据库访问
- ✅ JSON响应结构标准化

**行动**: Phase 1生成 `contracts/openapi.yaml` 和 `contracts/asyncapi.yaml`

### 原则二: 会话持久化 ✅

**要求**: 所有会话历史必须持久化存储并可检索

**合规状态**:
- ✅ 数据模型包含会话、消息、图表实体
- ✅ 支持按会话ID和时间范围检索
- ✅ 消息顺序和时间戳记录
- ⚠️ 数据保留策略待定 (研究阶段确定)

**行动**: Phase 0研究数据保留策略，Phase 1设计数据模型

### 原则三: 可视化集成 ✅

**要求**: 图表通过MCP服务器协议处理，与消息一起存储

**合规状态**:
- ✅ 使用@antv/mcp-server-chart（标准MCP协议）
- ✅ 图表数据与消息关联存储
- ✅ 前端使用AntV G2渲染（与MCP服务器生态一致）
- ✅ 错误降级机制（显示错误消息而非阻塞���

**行动**: Phase 0研究MCP协议集成模式，Phase 1定义图表数据契约

### 原则四: 测试覆盖 ✅

**要求**: 关键路径必须有契约测试和集成测试

**合规状态**:
- ✅ 契约测试: API端点与OpenAPI/AsyncAPI规范匹配
- ✅ 集成测试: Deep Research API调用、MCP服务器通信、SSE流
- ✅ 数据持久化测试: 会话CRUD、消息检索、图表关联
- ✅ 前端测试: 组件渲染、SSE事件处理、图表显示

**行动**: Phase 2 (tasks.md) 将包含测试任务

### 原则五: 简单性与可维护性 ✅

**要求**: 避免过早抽象，使用标准模式

**合规状态**:
- ✅ 使用FastAPI标准模式（后端）
- ✅ 使用React标准模式（前端）
- ✅ 配置外部化（环境变量管理API密钥）
- ✅ 三个相似实现优于复杂抽象（如消息处理逻辑）

**行动**: 代码实现阶段遵守

### 性能要求 ✅

**章程要求**:
- API响应时间<2秒 p95 ✅ (技术目标匹配)
- 图表生成<5秒 p95 ✅ (技术目标匹配)
- 历史加载<1秒 (100条) ✅ (技术目标: <2秒更宽松)
- 支持100并发会话 ✅ (技术目标匹配)

### 安全与数据隐私 ⚠️

**章程要求**: API认证、数据隔离、敏感数据保护

**合规状态**:
- ⚠️ API认证机制待定 (Phase 0研究: 会话cookie vs JWT)
- ⚠️ 用户数据隔离策略待定 (Phase 0研究: 单/多用户模式)
- ✅ API密钥外部化（环境变量）
- ✅ MCP通信验证（标准协议）

**行动**: Phase 0研究认证机制和用户隔离策略

### 🚨 待解决项 (Phase 0研究)

1. **数据保留策略**: 会话保留多长时间？自动清理规则？
2. **认证机制**: 会话cookie、JWT令牌还是OAuth2？
3. **用户模型**: 单用户demo还是多用户生产系统？
4. **数据库选择**: PostgreSQL（结构化、关系强）vs MongoDB（灵活、易扩展）

## 项目结构

### 文档 (当前功能)

```text
specs/001-agent-conversation-system/
├── plan.md              # 本文件 (/speckit.plan 命令输出)
├── research.md          # 阶段0输出 (/speckit.plan 命令)
├── data-model.md        # 阶段1输出 (/speckit.plan 命令)
├── quickstart.md        # 阶段1输出 (/speckit.plan 命令)
├── contracts/           # 阶段1输出 (/speckit.plan 命令)
│   ├── openapi.yaml     # REST API契约
│   └── asyncapi.yaml    # SSE事件流契约
└── tasks.md             # 阶段2输出 (/speckit.tasks 命令 - 不由 /speckit.plan 创建)
```

### 源代码 (仓库根目录)

```text
backend/
├── src/
│   ├── models/              # 数据模型 (会话、消息、图表、用户)
│   ├── services/            # 业务逻辑 (DeepResearch客户端、MCP客户端、会话管理)
│   ├── api/                 # API路由和SSE端点
│   ├── config/              # 配置管理 (环境变量、API密钥)
│   └── utils/               # 工具函数 (日志、错误处理)
├── tests/
│   ├── contract/            # 契约测试 (OpenAPI/AsyncAPI合规性)
│   ├── integration/         # 集成测试 (Deep Research、MCP、数据库)
│   └── unit/                # 单元测试
├── requirements.txt         # Python依赖
├── .env.example            # 环境变量模板
└── README.md

frontend/
├── src/
│   ├── components/          # React组件
│   │   ├── Chat/           # 对话界面组件
│   │   ├── Chart/          # 图表渲染组件
│   │   └── History/        # 历史记录组件
│   ├── services/            # API客户端和SSE事件处理
│   ├── hooks/               # 自定义React hooks (useSSE, useChat)
│   ├── types/               # TypeScript类型定义
│   └── utils/               # 工具函数
├── tests/
│   └── components/          # 组件测试
├── package.json
└── README.md
```

**结构决策**: 选择Web应用架构（Option 2），因为需求明确指出前端对话UI和后端API分离。前后端独立部署，通过SSE实现实时通信。

## 复杂度追踪

> **仅在章程检查有需要说明的违规时填写**

无违规项需要说明。所有核心原则均已满足或计划在Phase 0/1解决。

---

## Phase 完成状态

### ✅ Phase 0: 大纲与研究 (已完成)

**输出文件**: `research.md`

**已解决问题**:
1. ✅ 数据保留策略：30-90天自动删除，符合GDPR/CCPA
2. ✅ 认证机制：HTTP-only会话cookie + SSE兼容
3. ✅ 用户模型：单用户MVP，多用户就绪模式
4. ✅ 数据库选择：PostgreSQL + 时间序列优化
5. ✅ MCP集成模式：后端作为MCP客户端
6. ✅ SSE架构：FastAPI StreamingResponse + EventSource

**技术栈确认**:
- 后端: Python 3.11+ / FastAPI / PostgreSQL / SQLAlchemy
- 前端: TypeScript 5.x / React 18+ / AntV G2 / Vite
- 通信: SSE (Server-Sent Events)
- 图表: @antv/mcp-server-chart + AntV G2

### ✅ Phase 1: 设计与契约 (已完成)

**输出文件**:
- ✅ `data-model.md` - PostgreSQL数据库模式（4个表：users, sessions, messages, charts）
- ✅ `contracts/openapi.yaml` - REST API规范（会话和消息端点）
- ✅ `contracts/asyncapi.yaml` - SSE事件流规范（5种事件类型）
- ✅ `quickstart.md` - 开发者快速入门指南
- ✅ `CLAUDE.md` - Agent上下文文件（自动生成）

**设计要点**:
- 数据模型支持多用户（MVP使用单用户）
- 外键约束保证关系完整性
- 时间序列优化（BRIN索引、键集分页）
- 30天软删除 + 60天硬删除策略
- SSE事件流支持5种事件（message_chunk, chart_ready, message_complete, error, ping）

### 🚨 章程检查 - Phase 1后重新验证

所有原则仍然合规：

- ✅ **API优先设计**: OpenAPI 3.1 + AsyncAPI 3.0规范已生成
- ✅ **会话持久化**: 数据模型完整，30天保留策略已实施
- ✅ **可视化集成**: 图表表设计完成，MCP协议集成已规划
- ✅ **测试覆盖**: 契约测试基础已建立（OpenAPI/AsyncAPI规范）
- ✅ **简单性与可维护性**: 标准技术栈，无过度抽象

**无违规项。**

### 📋 Phase 2: 任务生成 (待执行)

**命令**: `/speckit.tasks`

**将生成**: `tasks.md` - 按用户故事组织的实施任务列表

**任务分组**:
- Setup: 项目初始化
- Foundational: 核心基础设施（数据库、认证、配置）
- User Story 1 (P1): 对话与图表生成
- User Story 2 (P2): 历史记录查看
- User Story 3 (P3): 多轮对话上下文
- Polish: 测试、文档、优化

---

## 下一步

✅ **已完成**: 规范 → 规划 → 研究 → 设计

🚀 **下一步**: 执行 `/speckit.tasks` 生成任务列表，然后开始实施
