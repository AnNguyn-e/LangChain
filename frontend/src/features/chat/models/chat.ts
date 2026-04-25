// Domain models for chat feature

export interface ChatSession {
  id: number;
  title: string;
  created_at?: string;
  summary?: string | null;
}

export type ChatRole = 'user' | 'ai';

export interface ChatMessage {
  id?: number;
  role: ChatRole;
  content: string;
  sources?: string[];
}

export interface RawChatMessage {
  id: number;
  question: string;
  answer: string;
  sources: string | null;
  created_at: string;
}
