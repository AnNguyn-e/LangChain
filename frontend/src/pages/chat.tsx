import { useState, useRef, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { PanelLeft } from 'lucide-react';

import { isLoggedIn } from '@/lib/auth';
import { ToastContainer, createToastManager } from '@/components/Toast';
import {
  useChatSessions,
  useCreateSession,
  useSessionMessages,
  useStreamChat,
  ChatSidebar,
  MessageList,
  ChatInput,
} from '@/features/chat';
import type { ChatMessage } from '@/features/chat';

export default function ChatPage() {
  const router = useRouter();

  // ── UI state ────────────────────────────────────────────────
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const [toasts, setToasts] = useState<any[]>([]);

  const addToast = createToastManager(setToasts);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // ── Auth guard ───────────────────────────────────────────────
  useEffect(() => {
    if (typeof window !== 'undefined' && !isLoggedIn()) {
      router.replace('/login');
    }
  }, [router]);

  // ── Data hooks ───────────────────────────────────────────────
  const { data: sessions = [] } = useChatSessions();
  const { mutateAsync: createSessionAsync, isPending: creatingSession } = useCreateSession();
  useSessionMessages(activeSessionId, setMessages);

  const { sendMessage, isGenerating } = useStreamChat({
    onError: (msg) => addToast(msg, 'error'),
  });

  // ── Handlers ─────────────────────────────────────────────────
  const handleSelectSession = (id: number) => {
    if (id !== activeSessionId) setMessages([]);
    setActiveSessionId(id);
  };

  const handleCreateSession = async () => {
    const res = await createSessionAsync('Cuộc trò chuyện mới');
    setActiveSessionId(res.data.id);
    setMessages([]);
  };

  const handleSend = async () => {
    if (!input.trim() || isGenerating) return;
    const query = input.trim();
    setInput('');
    setAutoScroll(true);

    await sendMessage(query, activeSessionId, setMessages, (newId) => {
      setActiveSessionId(newId);
    });
  };

  const handleScroll = () => {
    const el = chatContainerRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    setAutoScroll(nearBottom);
  };

  return (
    <>
      <Head>
        <title>Chat – DocAI Local</title>
        <meta name="description" content="Trò chuyện với AI DocAI Local về tài liệu nội bộ" />
      </Head>

      <ToastContainer toasts={toasts} />

      <div className="chat-layout">
        {/* ── Sidebar ── */}
        {sidebarOpen && (
          <ChatSidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSelectSession={handleSelectSession}
            onCreateSession={handleCreateSession}
            onClose={() => setSidebarOpen(false)}
          />
        )}

        {/* ── Main area ── */}
        <main className="chat-main">
          <header className="chat-header">
            {!sidebarOpen && (
              <button
                id="sidebar-open-btn"
                onClick={() => setSidebarOpen(true)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  marginRight: 12,
                }}
                title="Mở sidebar"
              >
                <PanelLeft size={24} />
              </button>
            )}
            <div style={{ fontWeight: 600 }}>DocAI Assistant</div>
          </header>

          {/* ── Message List ── */}
          <div
            className="chat-messages"
            ref={chatContainerRef}
            onScroll={handleScroll}
          >
            <MessageList
              messages={messages}
              isGenerating={isGenerating}
              autoScroll={autoScroll}
            />
          </div>

          {/* ── Input ── */}
          <ChatInput
            value={input}
            onChange={setInput}
            onSend={handleSend}
            isGenerating={isGenerating}
          />
        </main>
      </div>
    </>
  );
}
