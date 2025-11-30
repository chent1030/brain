/**
 * 消息输入组件
 *
 * 用户输入消息的文本框和发送按钮
 */

import React, { useState, KeyboardEvent } from 'react';

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function MessageInput({
  onSend,
  disabled = false,
  placeholder = '输入您的问题...',
}: MessageInputProps) {
  const [input, setInput] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: '12px',
        alignItems: 'flex-end',
      }}
    >
      <div
        style={{
          flex: 1,
          position: 'relative',
          border: isFocused
            ? '2px solid #3370ff'
            : disabled
            ? '1px solid #e8e9eb'
            : '1px solid #c9cdd4',
          borderRadius: '12px',
          backgroundColor: disabled ? '#f7f8fa' : '#ffffff',
          transition: 'all 0.2s',
        }}
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          disabled={disabled}
          rows={3}
          style={{
            width: '100%',
            padding: '14px 16px',
            border: 'none',
            borderRadius: '12px',
            fontSize: '15px',
            resize: 'none',
            fontFamily: 'inherit',
            backgroundColor: 'transparent',
            color: '#1f2329',
            outline: 'none',
            lineHeight: '1.6',
          }}
        />
      </div>
      <button
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        style={{
          padding: '14px 24px',
          backgroundColor:
            disabled || !input.trim() ? '#c9cdd4' : '#3370ff',
          color: 'white',
          border: 'none',
          borderRadius: '12px',
          cursor: disabled || !input.trim() ? 'not-allowed' : 'pointer',
          fontSize: '15px',
          fontWeight: 600,
          transition: 'all 0.2s',
          height: '52px',
          flexShrink: 0,
        }}
        onMouseEnter={(e) => {
          if (!disabled && input.trim()) {
            e.currentTarget.style.backgroundColor = '#2b5dd8';
            e.currentTarget.style.transform = 'translateY(-1px)';
          }
        }}
        onMouseLeave={(e) => {
          if (!disabled && input.trim()) {
            e.currentTarget.style.backgroundColor = '#3370ff';
            e.currentTarget.style.transform = 'translateY(0)';
          }
        }}
      >
        {disabled ? '发送中...' : '发送'}
      </button>
    </div>
  );
}
