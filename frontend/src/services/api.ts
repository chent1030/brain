/**
 * API客户端
 *
 * 封装所有与后端API的HTTP交互
 */

import type {
  Session,
  SessionListResponse,
  CreateSessionRequest,
  UpdateSessionRequest,
  SessionStatsResponse,
  Message,
  MessageListResponse,
  CreateMessageRequest,
  CreateMessageResponse,
  PaginationParams,
  MessageQueryParams,
  APIError,
} from '../types/api';

// API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// API错误类
export class APIException extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(detail);
    this.name = 'APIException';
  }
}

// 通用请求函数
async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
    credentials: 'include', // 发送cookies(会话认证)
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorData: APIError = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch {
      // 解析JSON失败,使用默认错误消息
    }

    throw new APIException(response.status, errorDetail);
  }

  // 204 No Content不返回body
  if (response.status === 204) {
    return undefined as T;
  }

  return await response.json();
}

// ============== 会话API ==============

export const SessionAPI = {
  /**
   * 创建新会话
   */
  async create(request: CreateSessionRequest): Promise<Session> {
    return fetchAPI<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * 获取会话详情
   */
  async get(sessionId: string): Promise<Session> {
    return fetchAPI<Session>(`/sessions/${sessionId}`);
  },

  /**
   * 获取会话列表(分页)
   */
  async list(params?: PaginationParams): Promise<SessionListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.before) queryParams.set('before', params.before);

    const query = queryParams.toString();
    return fetchAPI<SessionListResponse>(`/sessions${query ? `?${query}` : ''}`);
  },

  /**
   * 更新会话标题
   */
  async update(sessionId: string, request: UpdateSessionRequest): Promise<Session> {
    return fetchAPI<Session>(`/sessions/${sessionId}`, {
      method: 'PATCH',
      body: JSON.stringify(request),
    });
  },

  /**
   * 删除会话(软删除)
   */
  async delete(sessionId: string): Promise<void> {
    return fetchAPI<void>(`/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  },

  /**
   * 获取会话统计
   */
  async getStats(): Promise<SessionStatsResponse> {
    return fetchAPI<SessionStatsResponse>('/sessions/stats/summary');
  },
};

// ============== 消息API ==============

export const MessageAPI = {
  /**
   * 发送用户消息
   */
  async create(
    sessionId: string,
    request: CreateMessageRequest
  ): Promise<CreateMessageResponse> {
    return fetchAPI<CreateMessageResponse>(`/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * 获取会话的消息列表
   */
  async list(
    sessionId: string,
    params?: MessageQueryParams
  ): Promise<MessageListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.after_sequence !== undefined)
      queryParams.set('after_sequence', params.after_sequence.toString());

    const query = queryParams.toString();
    return fetchAPI<MessageListResponse>(
      `/sessions/${sessionId}/messages${query ? `?${query}` : ''}`
    );
  },

  /**
   * 获取单条消息详情
   */
  async get(messageId: number): Promise<Message> {
    return fetchAPI<Message>(`/messages/${messageId}`);
  },
};

// ============== 健康检查API ==============

export const HealthAPI = {
  /**
   * 基础健康检查
   */
  async check(): Promise<{ status: string; timestamp: string }> {
    return fetchAPI<{ status: string; timestamp: string }>('/health');
  },

  /**
   * 就绪检查(包含数据库)
   */
  async ready(): Promise<{
    status: string;
    timestamp: string;
    checks: Record<string, string>;
  }> {
    return fetchAPI<{
      status: string;
      timestamp: string;
      checks: Record<string, string>;
    }>('/health/ready');
  },
};

// 导出默认API对象
export default {
  sessions: SessionAPI,
  messages: MessageAPI,
  health: HealthAPI,
};
