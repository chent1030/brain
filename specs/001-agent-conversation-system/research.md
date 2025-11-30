# 研究文档: AI对话系统技术决策

**功能**: AI对话系统
**日期**: 2025-11-24
**目的**: 解决技术上下文中的未决问题，为Phase 1设计提供基础

## 研究主题

### 1. 数据保留策略

**决策**: 实施30-90天默认保留期，支持用户控制的长期存储选项

**理由**:
- **行业标准**: Claude默认30天，ChatGPT无限期保留但提供30天临时模式。30-90天平衡了用户价值与隐私合规
- **法规合规**: GDPR要求"不超过必要时间"；CCPA/CPRA要求公布具体时限。30-90天策略同时满足两者
- **成本优化**: 30-90天后自动删除显著降低存储成本，同时保留用户实际需要的近期上下文
- **用户控制**: 提供"导出对话"功能，用户可主动保存重要会话

**考虑的替代方案**:
- **无限期存储** (ChatGPT模式): 因GDPR合规风险、存储成本增加和隐私问题被拒绝。罚款高达2000万欧元或4%营收
- **7天保留** (Claude API即将推出): 对演示/MVP产品来说太短，无法保持有意义的对话连续性

**实施要点**:
- Phase 1实施30天自动删除，明确通知用户
- 为每条消息存储删除时间戳
- 删除截止日期前提供"导出对话"功能
- 在隐私政策中记录保留期以满足CCPA要求
- 使用PostgreSQL的分区表优化旧数据查询性能

---

### 2. 认证机制

**决策**: 使用HTTP-only会话cookie，SSE连接的查询参数令牌作为回退

**理由**:
- **SSE兼容性**: 原生EventSource API自动发送同源请求的cookie，消除自定义头复杂性。Cookie与长连接SSE无缝配合
- **安全最佳实践**: HTTP-only cookie防止XSS攻击（JWT存储在localStorage则无法防止）。基于会话的认证更易撤销，不在浏览器存储中暴露令牌
- **实施简单性**: FastAPI会话中间件自动处理cookie管理。MVP无需令牌刷新逻辑
- **长连接友好**: Cookie在SSE连接持续期间自动续约，无需客户端干预

**考虑的替代方案**:
- **JWT令牌**: 被拒绝，因为原生EventSource不支持自定义Authorization头，需要EventSourcePolyfill或基于fetch的变通方案。存储在localStorage时易受攻击
- **OAuth2**: 对单用户MVP来说过度设计，在此阶段增加显著复杂性而无明显好处
- **查询参数令牌**: 安全风险（出现在日志/URL中）。仅适合作为cookie被阻止时的回退

**实施要点**:
- Phase 1使用FastAPI的SessionMiddleware，配置secure、HTTP-only、SameSite=Lax cookie
- 设置合理的会话超时（24小时）
- SSE端点在打开连接前验证会话cookie
- 如后续出现扩展问题，考虑短期"SSE令牌"
- 记录会话ID用于审计和调试

---

### 3. 用户模型策略

**决策**: 首先构建单用户MVP，采用多用户就绪的数据库模式

**理由**:
- **开发速度**: MVP可提前2-4周启动，无需用户管理、认证复杂性和授权逻辑。先专注核心AI对话功能
- **降低迁移痛苦**: 从第一天起设计带`user_id`外键的数据库模式（即使硬编码为单用户）。后续添加多用户变成简单迁移
- **验证后再投资**: 在投资多租户基础设施（用户注册、密码重置、计费等）前验证对话系统价值
- **清晰升级路径**: 架构支持平滑过渡，避免推倒重来

**考虑的替代方案**:
- **从一开始就完整多用户**: 因MVP开发时间延长40-60%被拒绝。增加认证、授权、用户管理和测试复杂性，但不验证核心产品价值
- **纯单用户无迁移计划**: 危险 - 后续需要完整的模式重新设计

**实施要点**:
- Phase 1创建`users`表，包含单个硬编码用户
- 所有表包含`user_id`外键（但查询忽略它）
- 整个代码中使用`user_id = 1`常量
- Phase 2（MVP后）: 添加注册/登录端点，移除硬编码user_id，添加行级安全
- 迁移需要零数据库模式更改，仅需应用逻辑更新
- 使用环境变量控制单用户/多用户模式切换

---

### 4. 数据库选择

**决策**: 使用PostgreSQL（可选TimescaleDB扩展）

**理由**:
- **结构化对话数据**: 会话→消息→图表代表清晰的关系层次。PostgreSQL的外键、事务和连接完美建模此结构
- **优秀的时间序列性能**: 原生分区 + BRIN索引实现消息历史的<1ms查询时间。TimescaleDB扩展可在需要时添加hypertables实现90%+压缩
- **FastAPI生态系统**: SQLAlchemy + Alembic + asyncpg提供成熟的异步支持。比MongoDB（Motor/Beanie不够成熟）有更好的Python工具链
- **ACID保证**: 会话创建、消息追加、图表关联需要事务完整性

**考虑的替代方案**:
- **MongoDB**: 尽管有灵活性优势，但被拒绝。对话消息本质上是关系型的（会话→消息→图表）。失去外键、连接和事务使查询复杂化。时间序列性能相当但需要更多调优
- **混合方法**: 对MVP来说过度设计。增加运维复杂性（两个数据库）而无明显好处

**实施要点**:
- Phase 1使用PostgreSQL及以下优化:
  1. 索引`(session_id, created_at DESC)`用于消息分页
  2. `created_at`上的BRIN索引用于时间范围查询
  3. 键集分页（`WHERE id > last_id ORDER BY id LIMIT 50`）而非OFFSET/LIMIT
- 仅在存储>100万条消息或需要高级分析时考虑TimescaleDB扩展
- 使用SQLAlchemy异步模式配合连接池
- 配置适当的连接池大小（最大20连接用于10-50并发用户）
- 使用Alembic进行数据库迁移管理

---

### 5. MCP服务器集成模式

**决策**: 后端作为MCP客户端，通过标准MCP协议调用@antv/mcp-server-chart

**理由**:
- **标准协议**: MCP（模型上下文协议）是开放标准，确保与@antv/mcp-server-chart的互操作性
- **后端集中控制**: 后端管理MCP通信，前端仅接收渲染就绪的图表数据。简化前端逻辑，避免跨域问题
- **错误处理**: 后端可捕获MCP服务器错误，优雅降级（返回文本说明而非空白）
- **图表数据持久化**: 后端接收MCP响应后存储图表配置，历史回放无需重新生成

**实施要点**:
- Phase 1实现MCP客户端库（Python）
- 定义图表请求/响应格式（遵循MCP协议）
- 后端将Deep Research结果解析为图表规格，发送给MCP服务器
- MCP服务器返回AntV G2配置，后端存储后通过SSE流式传输给前端
- 前端使用AntV G2直接渲染图表配置
- 超时设置: MCP请求5秒超时，失败时降级为文本描述

---

### 6. SSE流式传输架构

**决策**: 使用FastAPI的StreamingResponse，基于事件的消息格式

**理由**:
- **渐进式UI更新**: Deep Research结果逐步生成时，用户可实时看到内容（打字机效果）
- **原生浏览器支持**: EventSource API无需额外库，自动重连机制内置
- **服务器简单**: FastAPI的StreamingResponse处理长连接，异步生成器yield事件
- **带外通信**: SSE事件可包含元数据（如typing indicators、图表就绪通知）

**实施要点**:
- Phase 1使用SSE事件格式:
  ```
  event: message_chunk
  data: {"content": "部分文本..."}

  event: chart_ready
  data: {"chart_id": "123", "config": {...}}

  event: message_complete
  data: {"message_id": "456"}
  ```
- FastAPI异步生成器:
  ```python
  async def stream_response():
      async for chunk in deep_research_client.stream():
          yield f"data: {json.dumps(chunk)}\n\n"
  ```
- 前端EventSource监听器处理不同事件类型
- 连接保活: 每30秒发送心跳事件（`:ping\n\n`）
- 错误处理: 连接断开时前端自动重连，后端恢复流式传输

---

## 技术栈最终确认

基于以上研究，Phase 1设计使用以下技术栈:

### 后端
- **框架**: FastAPI 0.115+ (异步支持，SSE StreamingResponse)
- **语言**: Python 3.11+
- **数据库**: PostgreSQL 15+ + asyncpg驱动
- **ORM**: SQLAlchemy 2.0 (异步模式) + Alembic (迁移)
- **认证**: FastAPI SessionMiddleware + HTTP-only cookies
- **Deep Research**: 通义SDK (官方Python客户端)
- **MCP客户端**: 自定义实现或社区库（如有）

### 前端
- **框架**: React 18+ (Hooks API)
- **语言**: TypeScript 5.x
- **构建工具**: Vite 5.x
- **图表**: AntV G2 5.x (与@antv/mcp-server-chart生态一致)
- **SSE**: 原生EventSource API
- **状态管理**: React Context + useReducer (避免Redux复杂性)
- **UI组件**: Ant Design 5.x (与AntV生态集成良好)

### 开发工具
- **代码质量**: Black (Python格式化), ESLint + Prettier (TypeScript格式化)
- **测试**: pytest + httpx (后端), Jest + RTL (前端)
- **API文档**: OpenAPI 3.1 (自动生成), AsyncAPI 3.0 (SSE规范)
- **容器化**: Docker + Docker Compose (本地开发)

---

## Phase 1设计清单

基于研究结论，Phase 1需要生成以下文档:

1. **data-model.md**: PostgreSQL数据库模式
   - `users`表（单用户，为多用户准备）
   - `sessions`表（对话会话）
   - `messages`表（用户和AI消息）
   - `charts`表（图表数据和配置）
   - 索引和约束
   - 30天自动删除触发器

2. **contracts/openapi.yaml**: REST API规范
   - POST /api/sessions (创建会话)
   - GET /api/sessions (列出会话)
   - GET /api/sessions/{id} (获取会话详情)
   - POST /api/sessions/{id}/messages (发送消息)
   - GET /api/sessions/{id}/messages (获取历史消息)

3. **contracts/asyncapi.yaml**: SSE事件流规范
   - `/api/sessions/{id}/stream` (SSE端点)
   - 事件类型: message_chunk, chart_ready, message_complete, error

4. **quickstart.md**: 开发者快速入门
   - 环境配置（Python、Node.js、PostgreSQL）
   - 本地开发启动步骤
   - API密钥配置（通义、MCP服务器）
   - 测试运行指南

---

## 未解决问题（后续阶段）

以下问题延后到实施阶段或生产部署:

1. **部署架构**: 容器化 vs 传统部署，CI/CD管道
2. **监控和日志**: 应用性能监控（APM），错误追踪
3. **扩展策略**: 负载均衡，数据库读写分离，缓存层
4. **备份和恢复**: 数据库备份策略，灾难恢复计划

这些问题在MVP验证后再投资更合理。
