import React, { useRef, useEffect } from 'react';
import { Bot } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import type { ChatMessage } from '../models/chat';

interface MessageListProps {
  messages: ChatMessage[];
  isGenerating: boolean;
  autoScroll: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isGenerating,
  autoScroll,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isGenerating, autoScroll]);

  if (messages.length === 0) {
    return (
      <div
        style={{
          textAlign: 'center',
          color: 'var(--text-muted)',
          marginTop: '20vh',
        }}
      >
        <Bot size={48} style={{ opacity: 0.2, marginBottom: 16 }} />
        <h2>Hôm nay tôi có thể giúp gì cho bạn?</h2>
      </div>
    );
  }

  return (
    <>
      {messages.map((msg, i) => {
        const isLastAI = msg.role === 'ai' && i === messages.length - 1;
        return (
          <MessageBubble
            key={i}
            message={msg}
            isLastAI={isLastAI}
            isGenerating={isGenerating}
          />
        );
      })}
      <div ref={bottomRef} />
    </>
  );
};
