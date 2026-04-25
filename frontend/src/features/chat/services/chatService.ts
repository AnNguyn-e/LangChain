// Infrastructure layer — only API calls, no business logic

import api from '@/lib/api';
import type { ChatSession, RawChatMessage } from '../models/chat';

const STREAM_BASE_URL =
  typeof window !== 'undefined'
    ? (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api').replace(/\/+$/, '')
    : 'http://localhost:8000/api';

export const chatService = {
  getSessions: (): Promise<{ data: ChatSession[] }> => api.get('/chat/sessions'),

  createSession: (title: string): Promise<{ data: ChatSession }> =>
    api.post('/chat/sessions', { title }),

  getMessages: (sessionId: number): Promise<{ data: RawChatMessage[] }> =>
    api.get(`/chat/sessions/${sessionId}/messages`),

  /**
   * Returns a fetch Response for streaming SSE
   */
  streamChat: async (sessionId: number, query: string): Promise<Response> => {
    const token = typeof window !== 'undefined'
      ? localStorage.getItem('auth_token')
      : null;

    return fetch(`${STREAM_BASE_URL}/chat/sessions/${sessionId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ query }),
    });
  },
};
