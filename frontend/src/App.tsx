/**
 * 主应用组件
 *
 * 集成历史记录侧边栏和对话界面
 */

import React, { useState, useEffect } from 'react';
import { SessionAPI } from './services/api';
import ChatContainer from './components/Chat/ChatContainer';
import HistoryList from './components/History/HistoryList';
import ErrorBoundary from './components/ErrorBoundary';

export default function App() {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(true);
  const [isInitializing, setIsInitializing] = useState(true);
  const [initError, setInitError] = useState<string | null>(null);

  // 初始化:创建或加载会话
  useEffect(() => {
    const initializeSession = async () => {
      try {
        setIsInitializing(true);
        setInitError(null);

        // 尝试获取现有会话列表
        const response = await SessionAPI.list({ limit: 1 });

        if (response.sessions.length > 0) {
          // 使用最新会话
          setCurrentSessionId(response.sessions[0].id);
        } else {
          // 创建新会话
          const newSession = await SessionAPI.create({ title: '新对话' });
          setCurrentSessionId(newSession.id);
        }
      } catch (error) {
        console.error('初始化会话失败:', error);
        setInitError(error instanceof Error ? error.message : '初始化失败');

        // 即使失败也创建一个临时会话ID，让用户能看到界面
        // 用户可以稍后点击"新对话"重试
        setCurrentSessionId('temp-session-' + Date.now());
      } finally {
        setIsInitializing(false);
      }
    };

    initializeSession();
  }, []);

  const handleNewChat = async () => {
    try {
      const newSession = await SessionAPI.create({ title: '新对话' });
      setCurrentSessionId(newSession.id);
    } catch (error) {
      console.error('创建新会话失败:', error);
    }
  };

  return (
    <ErrorBoundary>
      <div
        style={{
          display: 'flex',
          width: '100%',
          height: '100%',
          overflow: 'hidden',
          backgroundColor: '#f7f8fa',
        }}
      >
        {/* 侧边栏 - 历史记录 */}
        {showHistory && (
          <div
            style={{
              width: '280px',
              backgroundColor: '#ffffff',
              borderRight: '1px solid #e8e9eb',
              display: 'flex',
              flexDirection: 'column',
              flexShrink: 0,
            }}
          >
            <div
              style={{
                padding: '20px 16px',
                borderBottom: '1px solid #e8e9eb',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <h2
                style={{
                  margin: 0,
                  fontSize: '16px',
                  fontWeight: 600,
                  color: '#1f2329',
                }}
              >
                历史对话
              </h2>
              <button
                onClick={handleNewChat}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#3370ff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 500,
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#2b5dd8';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#3370ff';
                }}
              >
                + 新对话
              </button>
            </div>

            <HistoryList
              onSessionSelect={setCurrentSessionId}
              activeSessionId={currentSessionId || undefined}
            />
          </div>
        )}

        {/* 主内容区 - 对话界面 */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            minWidth: 0,
          }}
        >
          <div
            style={{
              padding: '16px 24px',
              backgroundColor: '#ffffff',
              borderBottom: '1px solid #e8e9eb',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexShrink: 0,
            }}
          >
            <h1
              style={{
                margin: 0,
                fontSize: '18px',
                fontWeight: 600,
                color: '#1f2329',
                letterSpacing: '-0.01em',
              }}
            >
              🧠 Brain AI
            </h1>
            <button
              onClick={() => setShowHistory(!showHistory)}
              style={{
                padding: '8px 16px',
                backgroundColor: '#f2f3f5',
                color: '#646a73',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#e5e6eb';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#f2f3f5';
              }}
            >
              {showHistory ? '隐藏' : '显示'}侧边栏
            </button>
          </div>

          {isInitializing ? (
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#8f959e',
                gap: '16px',
              }}
            >
              <div style={{ fontSize: '32px' }}>⏳</div>
              <div style={{ fontSize: '16px', fontWeight: 500 }}>正在初始化...</div>
              <div style={{ fontSize: '13px', color: '#c9cdd4' }}>
                请确保后端服务已启动 (http://localhost:8000)
              </div>
            </div>
          ) : initError ? (
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '20px',
                padding: '40px',
              }}
            >
              <div style={{ fontSize: '48px' }}>⚠️</div>
              <div style={{ color: '#f54a45', fontSize: '18px', fontWeight: 600 }}>
                连接失败
              </div>
              <div
                style={{
                  color: '#646a73',
                  textAlign: 'center',
                  maxWidth: '500px',
                  lineHeight: '1.6',
                }}
              >
                无法连接到后端服务。请检查：
                <ul
                  style={{
                    textAlign: 'left',
                    marginTop: '16px',
                    paddingLeft: '20px',
                  }}
                >
                  <li>后端服务是否已启动 (http://localhost:8000)</li>
                  <li>PostgreSQL 数据库是否正常运行</li>
                  <li>环境变量配置是否正确 (.env 文件)</li>
                </ul>
              </div>
              <div
                style={{
                  backgroundColor: '#fff1f0',
                  border: '1px solid #ffccc7',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  color: '#cf1322',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                  maxWidth: '500px',
                  wordBreak: 'break-word',
                }}
              >
                {initError}
              </div>
              <button
                onClick={handleNewChat}
                style={{
                  padding: '12px 24px',
                  backgroundColor: '#3370ff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 500,
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#2b5dd8';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#3370ff';
                }}
              >
                重试
              </button>
            </div>
          ) : currentSessionId ? (
            <ChatContainer key={currentSessionId} sessionId={currentSessionId} />
          ) : (
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#8f959e',
                gap: '16px',
              }}
            >
              <div style={{ fontSize: '48px' }}>💬</div>
              <div style={{ fontSize: '16px' }}>请点击"+ 新对话"开始</div>
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
}
