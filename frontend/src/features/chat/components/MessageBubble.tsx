import React from 'react';
import { Bot, User } from 'lucide-react';
import { MarkdownBlock } from './MarkdownBlock';
import type { ChatMessage } from '../models/chat';

interface MessageBubbleProps {
  message: ChatMessage;
  isLastAI: boolean;
  isGenerating: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  isLastAI,
  isGenerating,
}) => {
  const isAI = message.role === 'ai';

  return (
    <div className="message-row">
      <div className={`message-avatar ${message.role}`}>
        {isAI ? <Bot size={20} /> : <User size={20} />}
      </div>

      <div className="message-content">
        <div style={{ fontWeight: 600, marginBottom: 4 }}>
          {isAI ? 'DocAI' : 'Bạn'}
        </div>

        {isAI ? (
          <>
            {message.content === '' && isGenerating && isLastAI ? (
              <span className="blink">● ● ●</span>
            ) : (
              <MarkdownBlock content={message.content} />
            )}

            {message.sources && message.sources.length > 0 && (
              <div
                style={{
                  marginTop: 12,
                  fontSize: 13,
                  background: 'var(--bg-card)',
                  padding: '8px 12px',
                  borderRadius: 6,
                  border: '1px solid var(--border)',
                }}
              >
                <strong style={{ color: 'var(--text-secondary)' }}>
                  📚 Nguồn tài liệu:
                </strong>
                <ul style={{ margin: '4px 0 0 20px', color: 'var(--text-muted)' }}>
                  {message.sources.map((s, idx) => (
                    <li key={idx}>{s}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
        )}
      </div>
    </div>
  );
};
