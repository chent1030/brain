/**
 * SSE (Server-Sent Events) Hook
 *
 * 封装EventSource,用于接收服务器流式推送
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type {
  SSEEventType,
  MessageChunkEvent,
  ChartReadyEvent,
  MessageCompleteEvent,
  ErrorEvent,
} from '../types/api';

// SSE基础URL
const SSE_BASE_URL = import.meta.env.VITE_SSE_BASE_URL || 'http://localhost:8000/api';

export interface UseSSEOptions {
  /**
   * 事件监听器
   */
  onMessageChunk?: (data: MessageChunkEvent) => void;
  onChartReady?: (data: ChartReadyEvent) => void;
  onMessageComplete?: (data: MessageCompleteEvent) => void;
  onError?: (data: ErrorEvent) => void;
  onConnectionError?: (error: Event) => void;

  /**
   * 连接配置
   */
  autoConnect?: boolean; // 是否自动连接
  reconnectDelay?: number; // 重连延迟(毫秒)
  maxReconnectAttempts?: number; // 最大重连次数
}

export interface UseSSEReturn {
  /**
   * 连接状态
   */
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;

  /**
   * 控制函数
   */
  connect: (sessionId: string, query: string) => void;
  disconnect: () => void;

  /**
   * 累积数据(用于流式文本)
   */
  accumulatedContent: string;
  resetContent: () => void;
}

/**
 * SSE Hook
 *
 * 使用示例:
 * ```tsx
 * const { connect, disconnect, isConnected, accumulatedContent } = useSSE({
 *   onMessageChunk: (data) => console.log(data.content),
 *   onChartReady: (data) => console.log('Chart ready:', data.chart_id),
 *   onMessageComplete: (data) => console.log('Complete:', data.message_id),
 * });
 *
 * // 开始流式传输
 * connect('session-uuid', '用户问题');
 *
 * // 停止连接
 * disconnect();
 * ```
 */
export function useSSE(options: UseSSEOptions = {}): UseSSEReturn {
  const {
    onMessageChunk,
    onChartReady,
    onMessageComplete,
    onError,
    onConnectionError,
    autoConnect = false,
    reconnectDelay = 3000,
    maxReconnectAttempts = 3,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accumulatedContent, setAccumulatedContent] = useState('');

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * 重置累积内容
   */
  const resetContent = useCallback(() => {
    setAccumulatedContent('');
  }, []);

  /**
   * 断开连接
   */
  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  /**
   * 连接到SSE流
   */
  const connect = useCallback(
    (sessionId: string, query: string) => {
      // 清除旧连接
      disconnect();

      // 重置状态
      setError(null);
      setAccumulatedContent('');
      setIsConnecting(true);

      // 构建SSE URL (支持模式参数)
      const url = new URL(`${SSE_BASE_URL}/sessions/${sessionId}/stream`);
      url.searchParams.set('query', query);
      // 默认使用 hybrid 模式，可以通过额外参数传入
      // url.searchParams.set('mode', 'hybrid'); // 可选：pure_deep_research, pure_langchain, hybrid

      // 创建EventSource
      const eventSource = new EventSource(url.toString(), {
        withCredentials: true, // 发送cookies
      });

      eventSourceRef.current = eventSource;

      // 连接成功
      eventSource.addEventListener('open', () => {
        console.log('✅ SSE连接成功');
        setIsConnected(true);
        setIsConnecting(false);
        reconnectAttemptsRef.current = 0;
      });

      // 监听所有消息（调试用）
      eventSource.onmessage = (event) => {
        console.log('📨 收到SSE消息:', {
          type: event.type,
          data: event.data,
          lastEventId: event.lastEventId,
        });
      };

      // message_chunk事件
      eventSource.addEventListener('message_chunk', (event) => {
        console.log('📝 message_chunk事件:', event.data);
        try {
          const data: MessageChunkEvent = JSON.parse(event.data);

          // 累积内容
          setAccumulatedContent((prev) => prev + data.content);

          // 触发回调
          onMessageChunk?.(data);
        } catch (err) {
          console.error('解析message_chunk事件失败:', err);
        }
      });

      // chart_ready事件
      eventSource.addEventListener('chart_ready', (event) => {
        try {
          const data: ChartReadyEvent = JSON.parse(event.data);
          onChartReady?.(data);
        } catch (err) {
          console.error('解析chart_ready事件失败:', err);
        }
      });

      // message_complete事件
      eventSource.addEventListener('message_complete', (event) => {
        console.log('✅ 消息完成:', event.data);
        try {
          const data: MessageCompleteEvent = JSON.parse(event.data);
          onMessageComplete?.(data);

          // 完成后自动断开，不触发错误处理
          if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
          }
          setIsConnected(false);
          setIsConnecting(false);
        } catch (err) {
          console.error('解析message_complete事件失败:', err);
        }
      });

      // error事件(来自服务器)
      eventSource.addEventListener('error', (event: any) => {
        try {
          const data: ErrorEvent = JSON.parse(event.data);
          setError(data.error_message);
          onError?.(data);

          // 错误后断开
          disconnect();
        } catch (err) {
          // 这是EventSource的连接错误,不是服务器发送的error事件
        }
      });

      // ping事件(心跳,忽略)
      eventSource.addEventListener('ping', () => {
        // 保持连接,无需处理
      });

      // 连接错误
      eventSource.onerror = (event) => {
        console.log('SSE onerror 触发:', {
          readyState: eventSource.readyState,
          event,
        });

        // 如果是 CLOSED 状态 (2)，可能是正常关闭，不需要报错
        if (eventSource.readyState === EventSource.CLOSED) {
          console.log('SSE连接已关闭（正常）');
          setIsConnected(false);
          setIsConnecting(false);
          return;
        }

        console.error('SSE连接错误:', event);

        setIsConnected(false);
        setIsConnecting(false);

        onConnectionError?.(event);

        // 尝试重连
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;

          setError(
            `连接断开,${reconnectDelay / 1000}秒后重试(${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            connect(sessionId, query);
          }, reconnectDelay);
        } else {
          setError('连接失败,已达到最大重试次数');
          disconnect();
        }
      };
    },
    [
      disconnect,
      onMessageChunk,
      onChartReady,
      onMessageComplete,
      onError,
      onConnectionError,
      reconnectDelay,
      maxReconnectAttempts,
    ]
  );

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    isConnecting,
    error,
    connect,
    disconnect,
    accumulatedContent,
    resetContent,
  };
}
