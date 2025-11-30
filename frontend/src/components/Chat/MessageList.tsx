/**
 * 消息列表组件
 *
 * 显示所有历史消息和流式消息
 * 支持自动滚动到最新消息
 */

import React, { useEffect, useRef } from 'react';
import type { Message, Chart } from '../../types/api';
import MessageBubble from './MessageBubble';

interface MessageListProps {
  messages: Message[];
  streamingMessage?: { content: string; charts: Chart[] } | null;
  isLoading?: boolean;
}

export default function MessageList({
  messages,
  streamingMessage,
  isLoading = false,
}: MessageListProps) {
  // 用于自动滚动到底部
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // 当消息列表变化或流式消息更新时，自动滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage?.content]);

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
        加载中...
      </div>
    );
  }

  if (messages.length === 0 && !streamingMessage) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
        还没有消息,开始对话吧!
      </div>
    );
  }

  return (
    <div ref={containerRef} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {streamingMessage && (
        <MessageBubble
          message={{
            id: -1, // 临时ID
            session_id: '',
            role: 'assistant',
            content: streamingMessage.content,
            sequence: -1,
            metadata: null,
            created_at: new Date().toISOString(),
            charts: streamingMessage.charts,
          }}
          isStreaming={true}
        />
      )}

      {/* 用于滚动到底部的锚点 */}
      <div ref={messagesEndRef} />
    </div>
  );
}
