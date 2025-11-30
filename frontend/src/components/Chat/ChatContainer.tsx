/**
 * Chat容器组件
 *
 * 管理整个对话界面的状态和逻辑
 */

import React, { useState, useEffect, useCallback } from 'react';
import { MessageAPI } from '../../services/api';
import { useSSE } from '../../hooks/useSSE';
import type { Message, Chart } from '../../types/api';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

interface ChatContainerProps {
  sessionId: string;
}

export default function ChatContainer({ sessionId }: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // 流式AI响应的临时消息
  const [streamingMessage, setStreamingMessage] = useState<{
    content: string;
    charts: Chart[];
  } | null>(null);

  // SSE Hook
  const { connect, isConnected, error: sseError, accumulatedContent, resetContent } = useSSE({
    onMessageChunk: (data) => {
      // 累积内容会自动在accumulatedContent中更新
    },
    onChartReady: (data) => {
      // 添加图表到流式消息
      setStreamingMessage((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          charts: [
            ...prev.charts,
            {
              id: data.chart_id,
              chart_type: data.chart_type,
              chart_config: data.chart_config,
              sequence: data.sequence,
              created_at: new Date().toISOString(),
            },
          ],
        };
      });
    },
    onMessageComplete: async (data) => {
      // 消息完成,重新加载消息列表
      setStreamingMessage(null);
      resetContent();
      setIsSending(false);
      await loadMessages();
    },
    onError: (data) => {
      console.error('SSE错误:', data);
      setStreamingMessage(null);
      resetContent();
      setIsSending(false);
    },
  });

  // 加载消息列表
  const loadMessages = useCallback(async () => {
    // 如果是临时会话ID（离线模式），跳过加载
    if (sessionId.startsWith('temp-session-')) {
      setIsLoading(false);
      setLoadError('离线模式：无法连接到服务器');
      return;
    }

    try {
      setIsLoading(true);
      setLoadError(null);
      const response = await MessageAPI.list(sessionId);
      setMessages(response.messages);
    } catch (error) {
      console.error('加载消息失败:', error);
      setLoadError(error instanceof Error ? error.message : '加载失败');
      // 即使加载失败，也允许用户输入新消息
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // 初始加载
  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  // 更新流式消息内容 - 每次 accumulatedContent 变化时都更新
  useEffect(() => {
    if (isSending) {
      setStreamingMessage((prev) => ({
        content: accumulatedContent,
        charts: prev?.charts || [],
      }));
    }
  }, [accumulatedContent, isSending]);

  // 发送消息
  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isSending) return;

    try {
      setIsSending(true);

      // 创建用户消息
      await MessageAPI.create(sessionId, { content });

      // 重新加载消息(包含新创建的用户消息)
      await loadMessages();

      // 初始化流式消息
      setStreamingMessage({ content: '', charts: [] });
      resetContent();

      // 开始SSE连接获取AI响应
      connect(sessionId, content);
    } catch (error) {
      console.error('发送消息失败:', error);
      setIsSending(false);
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {/* 消息列表区域 - 可滚动 */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: '24px',
          backgroundColor: '#f7f8fa',
        }}
      >
        {loadError && (
          <div
            style={{
              backgroundColor: '#fff7e6',
              border: '1px solid #ffd591',
              borderRadius: '12px',
              padding: '16px 20px',
              marginBottom: '20px',
              color: '#d46b08',
              fontSize: '14px',
              lineHeight: '1.5',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
            }}
          >
            <span style={{ fontSize: '18px', flexShrink: 0 }}>⚠️</span>
            <div>
              <div style={{ fontWeight: 600, marginBottom: '4px' }}>{loadError}</div>
              <div style={{ fontSize: '13px', color: '#ad6800' }}>
                请检查后端连接状态
              </div>
            </div>
          </div>
        )}
        <MessageList
          messages={messages}
          streamingMessage={streamingMessage}
          isLoading={isLoading}
        />
      </div>

      {/* 输入框区域 - 固定在底部 */}
      <div
        style={{
          flexShrink: 0,
          borderTop: '1px solid #e8e9eb',
          backgroundColor: '#ffffff',
          padding: '20px 24px',
          boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.04)',
        }}
      >
        <MessageInput
          onSend={handleSendMessage}
          disabled={isSending || loadError !== null}
          placeholder={
            loadError
              ? '请先解决连接问题...'
              : isSending
              ? 'AI 正在思考中...'
              : '输入您的问题... (Shift + Enter 换行)'
          }
        />
        {sseError && (
          <div
            style={{
              color: '#f54a45',
              marginTop: '12px',
              fontSize: '13px',
              padding: '8px 12px',
              backgroundColor: '#fff1f0',
              borderRadius: '6px',
              border: '1px solid #ffccc7',
            }}
          >
            ❌ {sseError}
          </div>
        )}
        {loadError && (
          <div
            style={{
              color: '#8f959e',
              marginTop: '12px',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>💡</span>
            <span>提示: 请确保后端服务运行在 http://localhost:8000</span>
          </div>
        )}
      </div>
    </div>
  );
}
