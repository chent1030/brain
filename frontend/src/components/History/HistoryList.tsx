/**
 * 历史记录列表组件
 *
 * 显示用户的所有会话历史,支持无限滚动
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { SessionAPI } from '../../services/api';
import type { Session } from '../../types/api';
import SessionCard from './SessionCard';

interface HistoryListProps {
  onSessionSelect?: (sessionId: string) => void;
  activeSessionId?: string;
}

export default function HistoryList({ onSessionSelect, activeSessionId }: HistoryListProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const listRef = useRef<HTMLDivElement>(null);

  // 加载会话列表
  const loadSessions = useCallback(async (loadMore = false) => {
    try {
      if (loadMore) {
        setIsLoadingMore(true);
      } else {
        setIsLoading(true);
      }

      const before = loadMore && sessions.length > 0
        ? sessions[sessions.length - 1].updated_at
        : undefined;

      const response = await SessionAPI.list({
        limit: 20,
        before,
      });

      if (loadMore) {
        setSessions((prev) => [...prev, ...response.sessions]);
      } else {
        setSessions(response.sessions);
      }

      setHasMore(response.has_more);
    } catch (error) {
      console.error('加载会话列表失败:', error);
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, [sessions]);

  // 初始加载
  useEffect(() => {
    loadSessions();
  }, []);

  // 无限滚动
  const handleScroll = useCallback(() => {
    if (!listRef.current || !hasMore || isLoadingMore) return;

    const { scrollTop, scrollHeight, clientHeight } = listRef.current;
    if (scrollTop + clientHeight >= scrollHeight - 100) {
      loadSessions(true);
    }
  }, [hasMore, isLoadingMore, loadSessions]);

  if (isLoading) {
    return (
      <div
        style={{
          padding: '40px 20px',
          textAlign: 'center',
          color: '#8f959e',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '12px',
        }}
      >
        <div style={{ fontSize: '32px' }}>⏳</div>
        <div style={{ fontSize: '14px', fontWeight: 500 }}>加载中...</div>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div
        style={{
          padding: '60px 20px',
          textAlign: 'center',
          color: '#8f959e',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '12px',
        }}
      >
        <div style={{ fontSize: '48px' }}>💬</div>
        <div style={{ fontSize: '14px', fontWeight: 500, color: '#646a73' }}>
          还没有历史会话
        </div>
        <div style={{ fontSize: '12px', color: '#c9cdd4' }}>
          点击"+ 新对话"开始聊天
        </div>
      </div>
    );
  }

  return (
    <div
      ref={listRef}
      onScroll={handleScroll}
      style={{
        flex: 1,
        overflow: 'auto',
        padding: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}
    >
      {sessions.map((session) => (
        <SessionCard
          key={session.id}
          session={session}
          isActive={session.id === activeSessionId}
          onClick={() => onSessionSelect?.(session.id)}
        />
      ))}

      {isLoadingMore && (
        <div
          style={{
            padding: '16px',
            textAlign: 'center',
            color: '#8f959e',
            fontSize: '13px',
          }}
        >
          ⏳ 加载更多...
        </div>
      )}

      {!hasMore && sessions.length > 0 && (
        <div
          style={{
            padding: '16px',
            textAlign: 'center',
            color: '#c9cdd4',
            fontSize: '12px',
          }}
        >
          已加载全部会话
        </div>
      )}
    </div>
  );
}
