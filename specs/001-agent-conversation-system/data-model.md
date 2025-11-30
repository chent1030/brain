# 数据模型: AI对话系统

**功能**: AI对话系统
**数据库**: PostgreSQL 15+
**日期**: 2025-11-24

## 概述

本数据模型设计支持AI对话系统的核心功能：会话管理、消息存储、图表关联和历史检索。采用关系型设计，优化时间序列查询性能。

**设计原则**:
- 多用户就绪模式（MVP阶段使用单用户）
- 时间序列优化（BRIN索引、分区表）
- 外键约束保证数据完整性
- 30天自动删除策略

## 实体关系图

```
users (1) ----< sessions (N)
sessions (1) ----< messages (N)
messages (1) ----< charts (N)
```

## 表结构

### 1. users - 用户表

存储系统用户信息。MVP阶段仅包含单个硬编码用户。

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- MVP初始数据
INSERT INTO users (id, username, email)
VALUES (1, 'default_user', 'user@example.com');
```

**字段说明**:
- `id`: 用户唯一标识符（自增主键）
- `username`: 用户名（MVP阶段固定为"default_user"）
- `email`: 邮箱（可选，多用户阶段使用）
- `created_at`: 用户创建时间
- `last_active_at`: 最后活跃时间（用于统计分析）

**索引**:
```sql
CREATE INDEX idx_users_username ON users(username);
```

---

### 2. sessions - 会话表

存储对话会话信息。一个会话包含多条用户和AI消息。

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 分区表（按创建时间月份分区，便于自动删除旧数据）
CREATE TABLE sessions_partitioned (
    LIKE sessions INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- 创建最近3个月的分区
CREATE TABLE sessions_2025_11 PARTITION OF sessions_partitioned
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
CREATE TABLE sessions_2025_12 PARTITION OF sessions_partitioned
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
CREATE TABLE sessions_2026_01 PARTITION OF sessions_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

**字段说明**:
- `id`: 会话唯一标识符（UUID，避免序列号暴露信息）
- `user_id`: 所属用户ID（MVP阶段固定为1）
- `title`: 会话标题（可选，从首条消息生成摘要）
- `created_at`: 会话创建时间
- `updated_at`: 会话最后更新时间（新消息时触发）
- `deleted_at`: 软删除时间（30天保留策略）
- `message_count`: 消息计数（性能优化，避免COUNT查询）

**索引**:
```sql
-- 用户会话列表查询（按更新时间倒序）
CREATE INDEX idx_sessions_user_updated
    ON sessions(user_id, updated_at DESC)
    WHERE deleted_at IS NULL;

-- 软删除查询
CREATE INDEX idx_sessions_deleted
    ON sessions(deleted_at)
    WHERE deleted_at IS NOT NULL;

-- BRIN索引用于时间范围查询（高效、低空间占用）
CREATE INDEX idx_sessions_created_brin
    ON sessions USING BRIN(created_at);
```

**触发器**: 自动更新`updated_at`
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

### 3. messages - 消息表

存储用户和AI的对话消息。支持流式消息（逐步接收内容）。

```sql
CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sequence INTEGER NOT NULL,
    metadata JSONB,
    CONSTRAINT fk_messages_session FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- 分区表（按创建时间周分区，优化查询性能）
CREATE TABLE messages_partitioned (
    LIKE messages INCLUDING ALL
) PARTITION BY RANGE (created_at);
```

**字段说明**:
- `id`: 消息唯一标识符（自增主键）
- `session_id`: 所属会话ID
- `role`: 消息角色（'user' | 'assistant'）
- `content`: 消息内容（文本）
- `created_at`: 消息创建时间
- `sequence`: 会话内消息顺序（从0开始）
- `metadata`: 元数据（JSON格式，存储如：`{"tokens": 1234, "model": "deep-research-v1"}`）

**索引**:
```sql
-- 会话消息分页查询（键集分页，避免OFFSET性能问题）
CREATE INDEX idx_messages_session_sequence
    ON messages(session_id, sequence DESC);

-- 会话消息时间查询
CREATE INDEX idx_messages_session_created
    ON messages(session_id, created_at DESC);

-- BRIN索引用于全局时间范围查询
CREATE INDEX idx_messages_created_brin
    ON messages USING BRIN(created_at);
```

**触发器**: 自动递增sequence并更新会话message_count
```sql
CREATE OR REPLACE FUNCTION increment_message_sequence()
RETURNS TRIGGER AS $$
BEGIN
    -- 自动设置sequence为当前会话的最大sequence + 1
    SELECT COALESCE(MAX(sequence), -1) + 1
    INTO NEW.sequence
    FROM messages
    WHERE session_id = NEW.session_id;

    -- 更新会话message_count
    UPDATE sessions
    SET message_count = message_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.session_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_messages_sequence
    BEFORE INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION increment_message_sequence();
```

---

### 4. charts - 图表表

存储MCP服务器生成的图表配置和数据。

```sql
CREATE TABLE charts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id BIGINT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    chart_type VARCHAR(50) NOT NULL,
    chart_config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sequence INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT fk_charts_message FOREIGN KEY (message_id) REFERENCES messages(id)
);
```

**字段说明**:
- `id`: 图表唯一标识符（UUID）
- `message_id`: 所属消息ID（一条assistant消息可能包含多个图表）
- `chart_type`: 图表类型（如：'bar', 'line', 'pie', 'scatter'）
- `chart_config`: AntV G2图表配置（JSON格式，直接传给前端渲染）
- `created_at`: 图表创建时间
- `sequence`: 消息内图表顺序（从0开始）

**chart_config示例**:
```json
{
  "type": "bar",
  "data": [
    {"category": "A", "value": 30},
    {"category": "B", "value": 45}
  ],
  "xField": "category",
  "yField": "value",
  "title": "销售数据"
}
```

**索引**:
```sql
-- 消息图表查询
CREATE INDEX idx_charts_message
    ON charts(message_id, sequence);

-- 按图表类型查询（用于统计分析）
CREATE INDEX idx_charts_type
    ON charts(chart_type);
```

---

## 数据保留策略

### 30天自动删除

使用PostgreSQL的定时任务（pg_cron扩展）或应用层定时任务实现。

**软删除策略** (推荐):
```sql
-- 标记30天前的会话为已删除
UPDATE sessions
SET deleted_at = CURRENT_TIMESTAMP
WHERE created_at < (CURRENT_TIMESTAMP - INTERVAL '30 days')
  AND deleted_at IS NULL;
```

**硬删除策略** (生产环境):
```sql
-- 删除90天前的软删除会话（保留60天缓冲期）
DELETE FROM sessions
WHERE deleted_at < (CURRENT_TIMESTAMP - INTERVAL '60 days');
```

**定时任务配置** (pg_cron):
```sql
-- 安装pg_cron扩展
CREATE EXTENSION pg_cron;

-- 每天凌晨2点执行软删除
SELECT cron.schedule(
    'soft-delete-old-sessions',
    '0 2 * * *',
    $$UPDATE sessions
      SET deleted_at = CURRENT_TIMESTAMP
      WHERE created_at < (CURRENT_TIMESTAMP - INTERVAL '30 days')
        AND deleted_at IS NULL$$
);

-- 每周日凌晨3点执行硬删除
SELECT cron.schedule(
    'hard-delete-old-sessions',
    '0 3 * * 0',
    $$DELETE FROM sessions
      WHERE deleted_at < (CURRENT_TIMESTAMP - INTERVAL '60 days')$$
);
```

---

## 查询示例

### 1. 创建新会话并发送首条消息

```sql
-- 创建会话
INSERT INTO sessions (user_id, title)
VALUES (1, '关于AI市场的对话')
RETURNING id;

-- 插入用户消息
INSERT INTO messages (session_id, role, content)
VALUES ('会话UUID', 'user', '分析2024年全球AI市场趋势');
```

### 2. 获取用户会话列表（分页）

```sql
-- 键集分页（比OFFSET/LIMIT高效）
SELECT id, title, created_at, updated_at, message_count
FROM sessions
WHERE user_id = 1
  AND deleted_at IS NULL
  AND updated_at < '上一页最后一条的updated_at'
ORDER BY updated_at DESC
LIMIT 20;
```

### 3. 获取会话历史消息（含图表）

```sql
-- 使用LEFT JOIN获取消息及其关联的图表
SELECT
    m.id, m.role, m.content, m.created_at, m.sequence,
    json_agg(
        json_build_object(
            'id', c.id,
            'type', c.chart_type,
            'config', c.chart_config,
            'sequence', c.sequence
        ) ORDER BY c.sequence
    ) FILTER (WHERE c.id IS NOT NULL) AS charts
FROM messages m
LEFT JOIN charts c ON m.id = c.message_id
WHERE m.session_id = '会话UUID'
GROUP BY m.id, m.role, m.content, m.created_at, m.sequence
ORDER BY m.sequence;
```

### 4. 插入AI回复及图表

```sql
-- 插入assistant消息
INSERT INTO messages (session_id, role, content, metadata)
VALUES (
    '会话UUID',
    'assistant',
    'AI市场分析结果文本...',
    '{"model": "deep-research-v1", "tokens": 2048}'
)
RETURNING id;

-- 插入关联图表
INSERT INTO charts (message_id, chart_type, chart_config, sequence)
VALUES
    ('消息ID', 'line', '{"type": "line", "data": [...]}', 0),
    ('消息ID', 'bar', '{"type": "bar", "data": [...]}', 1);
```

---

## 数据库配置建议

### 连接池配置 (asyncpg)

```python
# 10-50并发用户
pool = await asyncpg.create_pool(
    dsn='postgresql://user:pass@localhost/dbname',
    min_size=5,
    max_size=20,
    command_timeout=60
)
```

### 性能优化配置

```sql
-- 优化查询规划器
SET random_page_cost = 1.1;  -- SSD存储
SET effective_cache_size = '4GB';  -- 根据服务器内存调整

-- 启用并行查询（大表扫描）
SET max_parallel_workers_per_gather = 4;
```

---

## 迁移计划

### Phase 1 → Phase 2 (多用户支持)

**数据库更改**: 无需更改模式，仅需应用逻辑更新

**步骤**:
1. 添加用户注册/登录端点
2. 移除代码中的`user_id = 1`硬编码
3. 添加行级安全策略（RLS）:
```sql
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY sessions_user_isolation
    ON sessions
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::BIGINT);
```

---

## 备份策略

**每日增量备份**:
```bash
pg_dump --format=custom --file=backup_$(date +%Y%m%d).dump dbname
```

**Point-in-Time Recovery (PITR)**:
```sql
-- 启用WAL归档
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
```

---

## 总结

本数据模型设计要点:
- ✅ 关系型结构保证数据完整性
- ✅ 时间序列优化（BRIN索引、分区表）
- ✅ 30天自动删除策略（软删除+硬删除）
- ✅ 多用户就绪（MVP使用单用户）
- ✅ 键集分页优化查询性能
- ✅ JSONB存储灵活元数据和图表配置
