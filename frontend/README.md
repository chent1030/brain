# Frontend - Brain AI 对话系统

React + TypeScript 前端应用,提供现代化的 AI 对话界面。

## 技术栈

- TypeScript 5.x
- React 18+
- Vite 5.x (构建工具)
- AntV G2 5.x (图表库)

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

## 项目结构

```
frontend/
├── src/
│   ├── components/       # React 组件
│   │   ├── Chat/         # 对话相关组件
│   │   │   ├── ChatContainer.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   ├── MessageList.tsx
│   │   │   └── MessageBubble.tsx
│   │   ├── Chart/        # 图表组件
│   │   │   └── ChartRenderer.tsx
│   │   ├── History/      # 历史记录组件
│   │   │   ├── HistoryList.tsx
│   │   │   └── SessionCard.tsx
│   │   └── ErrorBoundary.tsx  # 错误边界
│   ├── hooks/            # React Hooks
│   │   └── useSSE.ts     # SSE Hook
│   ├── services/         # API 客户端
│   │   └── api.ts
│   ├── types/            # TypeScript 类型
│   │   └── api.ts
│   ├── App.tsx           # 主应用
│   ├── main.tsx          # 入口文件
│   └── index.css         # 全局样式
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 可用脚本

```bash
# 开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint

# 类型检查
npm run type-check
```

## 组件说明

### ChatContainer
主对话容器,管理对话状态和 SSE 连接。

### MessageList
显示历史消息和流式消息列表。

### MessageBubble
单条消息气泡,区分用户消息和 AI 消息。

### MessageInput
消息输入框,支持 Enter 发送、Shift+Enter 换行。

### ChartRenderer
使用 AntV G2 渲染图表,支持 bar、line、pie、scatter 等类型。

### HistoryList
历史记录列表,支持无限滚动加载。

### ErrorBoundary
React 错误边界,捕获并显示组件错误。

## Hooks 说明

### useSSE
SSE 连接管理 Hook。

```typescript
const { connect, disconnect, isConnected, accumulatedContent } = useSSE({
  onMessageChunk: (data) => console.log(data.content),
  onChartReady: (data) => console.log(data.chart_id),
  onMessageComplete: (data) => console.log(data.message_id),
});

// 连接
connect(sessionId, query);

// 断开
disconnect();
```

## API 客户端

所有 API 调用通过 `src/services/api.ts` 统一管理:

```typescript
import { SessionAPI, MessageAPI } from './services/api';

// 创建会话
const session = await SessionAPI.create({ title: '新对话' });

// 获取会话列表
const { sessions, has_more } = await SessionAPI.list({ limit: 20 });

// 发送消息
await MessageAPI.create(sessionId, { content: '你好' });

// 获取消息历史
const { messages } = await MessageAPI.list(sessionId);
```

## 环境变量

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

## 开发指南

### 添加新组件

1. 在 `src/components/` 创建组件文件
2. 导出组件
3. 在需要的地方导入使用

### 添加新的 API 调用

1. 在 `src/types/api.ts` 定义类型
2. 在 `src/services/api.ts` 添加 API 函数
3. 在组件中使用

### 添加新的 Hook

1. 在 `src/hooks/` 创建 Hook 文件
2. 遵循 React Hooks 规则
3. 导出 Hook

## 构建和部署

```bash
# 构建生产版本
npm run build

# 输出在 dist/ 目录
```

部署 `dist/` 目录到任何静态文件服务器(Nginx, Vercel, Netlify 等)。

## 故障排除

### API 连接失败
- 检查后端是否运行
- 验证 `VITE_API_BASE_URL` 配置正确
- 检查 CORS 配置

### SSE 连接失败
- 验证 `VITE_SSE_BASE_URL` 配置正确
- 检查浏览器是否支持 EventSource
- 查看浏览器控制台错误信息

### 图表不显示
- 确认 `VITE_ENABLE_CHART=true`
- 检查 MCP 服务器是否运行
- 查看浏览器控制台错误信息
