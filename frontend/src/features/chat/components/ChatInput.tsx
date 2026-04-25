import React, { useRef } from 'react';
import { Send } from 'lucide-react';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isGenerating: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSend,
  isGenerating,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const handleSend = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    onSend();
  };

  return (
    <div className="chat-input-wrapper">
      <div className="chat-input-box">
        <textarea
          ref={textareaRef}
          id="chat-textarea"
          className="chat-textarea"
          placeholder={
            isGenerating
              ? 'AI đang trả lời...'
              : 'Hỏi bất cứ điều gì (Enter để gửi, Shift+Enter xuống dòng)...'
          }
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={isGenerating}
          rows={1}
        />
        <button
          id="chat-send-btn"
          className="chat-send-btn"
          onClick={handleSend}
          disabled={!value.trim() || isGenerating}
          title="Gửi"
        >
          <Send size={16} style={{ transform: 'translateX(-1px)' }} />
        </button>
      </div>
      <div
        style={{
          textAlign: 'center',
          fontSize: 11,
          color: 'var(--text-muted)',
          marginTop: 12,
        }}
      >
        Mọi thông tin do AI tự sinh cần được xác thực chéo nguồn dữ liệu.
      </div>
    </div>
  );
};
