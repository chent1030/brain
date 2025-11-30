/**
 * 消息气泡组件
 *
 * 显示单条消息(用户或AI)及其图表
 * 支持Markdown渲染
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '../../types/api';
import ChartRenderer from '../Chart/ChartRenderer';

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export default function MessageBubble({ message, isStreaming = false }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  const bubbleStyle: React.CSSProperties = {
    maxWidth: '75%',
    padding: '14px 18px',
    borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
    backgroundColor: isUser ? '#3370ff' : '#ffffff',
    color: isUser ? 'white' : '#1f2329',
    alignSelf: isUser ? 'flex-end' : 'flex-start',
    boxShadow: isUser
      ? '0 2px 8px rgba(51, 112, 255, 0.15)'
      : '0 2px 8px rgba(0, 0, 0, 0.05)',
    border: isUser ? 'none' : '1px solid #e8e9eb',
  };

  const containerStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: isUser ? 'flex-end' : 'flex-start',
    gap: '8px',
    marginBottom: '20px',
  };

  // Markdown样式
  const markdownStyle: React.CSSProperties = {
    wordBreak: 'break-word',
    lineHeight: '1.7',
    fontSize: '15px',
  };

  // 为用户消息使用纯文本，为AI消息使用Markdown
  const renderContent = () => {
    if (isUser) {
      // 用户消息使用纯文本显示
      return (
        <div
          style={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            lineHeight: '1.6',
            fontSize: '15px',
          }}
        >
          {message.content || ''}
        </div>
      );
    }

    // AI消息使用Markdown渲染
    return (
      <div style={markdownStyle} className="markdown-body">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // 自定义样式以适配深色/浅色背景
            p: ({ children }) => (
              <p style={{ margin: '0.6em 0', color: '#1f2329', lineHeight: '1.7' }}>
                {children}
              </p>
            ),
            h1: ({ children }) => (
              <h1
                style={{
                  margin: '0.8em 0 0.5em',
                  fontSize: '1.6em',
                  fontWeight: 600,
                  color: '#1f2329',
                }}
              >
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2
                style={{
                  margin: '0.8em 0 0.5em',
                  fontSize: '1.4em',
                  fontWeight: 600,
                  color: '#1f2329',
                }}
              >
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3
                style={{
                  margin: '0.8em 0 0.5em',
                  fontSize: '1.2em',
                  fontWeight: 600,
                  color: '#1f2329',
                }}
              >
                {children}
              </h3>
            ),
            ul: ({ children }) => (
              <ul
                style={{
                  margin: '0.6em 0',
                  paddingLeft: '1.8em',
                  color: '#1f2329',
                  lineHeight: '1.8',
                }}
              >
                {children}
              </ul>
            ),
            ol: ({ children }) => (
              <ol
                style={{
                  margin: '0.6em 0',
                  paddingLeft: '1.8em',
                  color: '#1f2329',
                  lineHeight: '1.8',
                }}
              >
                {children}
              </ol>
            ),
            li: ({ children }) => (
              <li style={{ margin: '0.4em 0', color: '#1f2329' }}>{children}</li>
            ),
            code: ({ children, className }) => {
              const isInline = !className;
              return (
                <code
                  style={{
                    backgroundColor: isInline ? '#f2f3f5' : '#2d2d2d',
                    color: isInline ? '#d03050' : '#f8f8f2',
                    padding: isInline ? '3px 7px' : '14px',
                    borderRadius: isInline ? '4px' : '8px',
                    fontSize: '0.9em',
                    fontFamily: 'JetBrains Mono, Monaco, Consolas, monospace',
                    display: isInline ? 'inline' : 'block',
                    overflowX: isInline ? 'visible' : 'auto',
                    margin: isInline ? '0' : '0.6em 0',
                    border: isInline ? '1px solid #e8e9eb' : 'none',
                  }}
                >
                  {children}
                </code>
              );
            },
            pre: ({ children }) => (
              <pre style={{ margin: '0.6em 0', overflow: 'visible' }}>{children}</pre>
            ),
            blockquote: ({ children }) => (
              <blockquote
                style={{
                  margin: '0.6em 0',
                  paddingLeft: '1.2em',
                  borderLeft: '4px solid #3370ff',
                  color: '#646a73',
                  fontStyle: 'italic',
                }}
              >
                {children}
              </blockquote>
            ),
            a: ({ children, href }) => (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  color: '#3370ff',
                  textDecoration: 'none',
                  borderBottom: '1px solid #3370ff',
                  transition: 'all 0.2s',
                }}
              >
                {children}
              </a>
            ),
            strong: ({ children }) => (
              <strong style={{ fontWeight: 600, color: '#1f2329' }}>{children}</strong>
            ),
            em: ({ children }) => (
              <em style={{ fontStyle: 'italic', color: '#646a73' }}>{children}</em>
            ),
          }}
        >
          {message.content || (isStreaming ? '思考中...' : '')}
        </ReactMarkdown>
      </div>
    );
  };

  return (
    <div style={containerStyle}>
      {/* 角色标签 */}
      <div
        style={{
          fontSize: '13px',
          color: '#8f959e',
          paddingLeft: '4px',
          fontWeight: 500,
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        <span>{isUser ? '👤' : '🤖'}</span>
        <span>{isUser ? '您' : 'AI 助手'}</span>
        {isStreaming && (
          <span
            style={{
              fontSize: '12px',
              color: '#3370ff',
              backgroundColor: '#e8f0ff',
              padding: '2px 8px',
              borderRadius: '12px',
            }}
          >
            正在回复...
          </span>
        )}
      </div>

      {/* 消息内容 */}
      <div style={bubbleStyle}>{renderContent()}</div>

      {/* 图表 */}
      {message.charts && message.charts.length > 0 && (
        <div
          style={{
            width: '100%',
            maxWidth: '700px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          {message.charts.map((chart) => (
            <ChartRenderer key={chart.id} chart={chart} />
          ))}
        </div>
      )}

      {/* 时间戳 */}
      {!isStreaming && (
        <div
          style={{
            fontSize: '12px',
            color: '#c9cdd4',
            paddingLeft: '4px',
            fontWeight: 400,
          }}
        >
          {new Date(message.created_at).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      )}
    </div>
  );
}
