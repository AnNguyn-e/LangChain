// Application layer — transform raw chat history to ChatMessage[]

import type { ChatMessage, RawChatMessage } from '../models/chat';

/**
 * Maps flat Q&A records from API into paired [user, ai] message tuples
 */
export const chatHistoryUseCase = {
  mapMessages: (raw: RawChatMessage[]): ChatMessage[] => {
    const messages: ChatMessage[] = [];

    for (const record of raw) {
      messages.push({ role: 'user', content: record.question });

      let sources: string[] = [];
      try {
        if (record.sources) {
          sources = JSON.parse(record.sources);
        }
      } catch {
        sources = [];
      }

      messages.push({ role: 'ai', content: record.answer, sources });
    }

    return messages;
  },
};
