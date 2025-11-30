/**
 * API类型定义
 *
 * 定义与后端API交互的所有类型
 */

// ============== 会话相关类型 ==============

export interface Session {
  id: string;
  user_id: number;
  title: string | null;
  message_count: number;
  created_at: string; // ISO 8601格式
  updated_at: string;
}

export interface SessionListResponse {
  sessions: Session[];
  has_more: boolean;
}

export interface CreateSessionRequest {
  title?: string;
}

export interface UpdateSessionRequest {
  title: string;
}

export interface SessionStatsResponse {
  total_sessions: number;
  total_messages: number;
}

// ============== 消息相关类型 ==============

export type MessageRole = 'user' | 'assistant';

export interface Chart {
  id: string;
  chart_type: string;
  chart_config: Record<string, any>; // AntV G2配置
  sequence: number;
  created_at: string;
}

export interface Message {
  id: number;
  session_id: string;
  role: MessageRole;
  content: string;
  sequence: number;
  metadata: Record<string, any> | null;
  created_at: string;
  charts: Chart[];
}

export interface MessageListResponse {
  messages: Message[];
}

export interface CreateMessageRequest {
  content: string;
}

export interface CreateMessageResponse {
  message_id: number;
  session_id: string;
  sequence: number;
}

// ============== SSE事件类型 ==============

export type SSEEventType =
  | 'message_chunk'
  | 'chart_ready'
  | 'message_complete'
  | 'error'
  | 'ping';

export interface MessageChunkEvent {
  content: string;
  is_final: boolean;
}

export interface ChartReadyEvent {
  chart_id: string;
  chart_type: string;
  chart_config: Record<string, any>;
  sequence: number;
}

export interface MessageCompleteEvent {
  message_id: number;
  sequence: number;
  total_charts: number;
}

export interface ErrorEvent {
  error_code: string;
  error_message: string;
}

export interface PingEvent {
  timestamp: number;
}

export type SSEEventData =
  | MessageChunkEvent
  | ChartReadyEvent
  | MessageCompleteEvent
  | ErrorEvent
  | PingEvent;

// ============== API错误类型 ==============

export interface APIError {
  detail: string;
  status_code?: number;
}

// ============== 辅助类型 ==============

export interface PaginationParams {
  limit?: number;
  before?: string; // ISO 8601格式的updated_at
}

export interface MessageQueryParams {
  limit?: number;
  after_sequence?: number;
}
