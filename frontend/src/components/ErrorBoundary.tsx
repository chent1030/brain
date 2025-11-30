/**
 * React错误边界组件
 *
 * 捕获子组件中的JavaScript错误并显示友好的错误界面
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // 更新state以便下一次渲染显示降级UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 记录错误到控制台或错误监控服务
    console.error('错误边界捕获到错误:', error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // 如果提供了自定义fallback,使用它
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认错误UI
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            padding: '20px',
            backgroundColor: '#f5f5f5',
          }}
        >
          <div
            style={{
              maxWidth: '600px',
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '32px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              textAlign: 'center',
            }}
          >
            <h1 style={{ color: '#ff4d4f', marginBottom: '16px' }}>
              抱歉,出现了一些问题
            </h1>

            <p style={{ color: '#666', marginBottom: '24px' }}>
              应用遇到了一个意外错误。请尝试刷新页面或联系技术支持。
            </p>

            {this.state.error && (
              <details
                style={{
                  marginBottom: '24px',
                  textAlign: 'left',
                  backgroundColor: '#fafafa',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                }}
              >
                <summary style={{ cursor: 'pointer', fontWeight: 'bold', marginBottom: '8px' }}>
                  错误详情
                </summary>
                <pre
                  style={{
                    margin: 0,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    color: '#ff4d4f',
                  }}
                >
                  {this.state.error.toString()}
                </pre>
                {this.state.errorInfo && (
                  <pre
                    style={{
                      margin: '8px 0 0 0',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      color: '#888',
                    }}
                  >
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </details>
            )}

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button
                onClick={this.handleReset}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#1890ff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold',
                }}
              >
                重试
              </button>

              <button
                onClick={() => window.location.reload()}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#f0f0f0',
                  color: '#333',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold',
                }}
              >
                刷新页面
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
