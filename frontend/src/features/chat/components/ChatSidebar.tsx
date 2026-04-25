import React from 'react';
import { useRouter } from 'next/router';
import { PanelLeftClose, Plus, MessageSquare, LogOut } from 'lucide-react';
import type { ChatSession } from '../models/chat';

interface ChatSidebarProps {
  sessions: ChatSession[];
  activeSessionId: number | null;
  onSelectSession: (id: number) => void;
  onCreateSession: () => void;
  onClose: () => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onClose,
}) => {
  const router = useRouter();

  return (
    <aside className="chat-sidebar">
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px',
        }}
      >
        <h3 style={{ margin: 0, fontSize: 16 }}>Lịch sử trò chuyện</h3>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
          }}
          title="Đóng sidebar"
        >
          <PanelLeftClose size={20} />
        </button>
      </div>

      <button
        id="new-chat-btn"
        className="chat-new-btn"
        onClick={onCreateSession}
      >
        <Plus size={18} /> Chat mới
      </button>

      <div className="chat-history">
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`chat-history-item${activeSessionId === s.id ? ' active' : ''}`}
            onClick={() => onSelectSession(s.id)}
          >
            <MessageSquare
              size={14}
              style={{
                display: 'inline',
                marginRight: 8,
                transform: 'translateY(2px)',
              }}
            />
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {s.title}
            </span>
            {s.summary && (
              <span
                title="Memory Active"
                style={{ fontSize: '0.6rem', color: '#60a5fa', marginLeft: 4 }}
              >
                🧠
              </span>
            )}
          </div>
        ))}
      </div>

      <div style={{ padding: '16px', borderTop: '1px solid var(--border)' }}>
        <button
          onClick={() => router.push('/')}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <LogOut size={16} /> Về Dashboard
        </button>
      </div>
    </aside>
  );
};
