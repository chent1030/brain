/**
 * 会话卡片组件
 *
 * 显示单个历史会话的预览信息
 */

import React from 'react';
import type { Session } from '../../types/api';

interface SessionCardProps {
  session: Session;
  isActive?: boolean;
  onClick?: () => void;
}

export default function SessionCard({ session, isActive = false, onClick }: SessionCardProps) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: '14px 16px',
        borderRadius: '10px',
        backgroundColor: isActive ? '#e8f0ff' : '#f7f8fa',
        border: isActive ? '2px solid #3370ff' : '1px solid transparent',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        if (!isActive) {
          e.currentTarget.style.backgroundColor = '#ffffff';
          e.currentTarget.style.borderColor = '#e8e9eb';
          e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.06)';
        }
      }}
      onMouseLeave={(e) => {
        if (!isActive) {
          e.currentTarget.style.backgroundColor = '#f7f8fa';
          e.currentTarget.style.borderColor = 'transparent';
          e.currentTarget.style.boxShadow = 'none';
        }
      }}
    >
      <div
        style={{
          fontWeight: 600,
          marginBottom: '8px',
          color: isActive ? '#3370ff' : '#1f2329',
          fontSize: '14px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {session.title || '未命名对话'}
      </div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '12px',
          color: isActive ? '#2b5dd8' : '#8f959e',
        }}
      >
        <span>💬 {session.message_count} 条消息</span>
        <span style={{ fontSize: '11px', color: '#c9cdd4' }}>
          {new Date(session.updated_at).toLocaleDateString('zh-CN', {
            month: 'short',
            day: 'numeric',
          })}
        </span>
      </div>
    </div>
  );
}
