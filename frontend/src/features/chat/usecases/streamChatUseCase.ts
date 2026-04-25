// Application layer — SSE streaming logic, isolated from UI

import type { ChatMessage } from '../models/chat';
import { chatService } from '../services/chatService';

export interface StreamCallbacks {
  onToken: (content: string) => void;
  onSources: (sources: string[]) => void;
  onDone: () => void;
  onError: (err: Error) => void;
}

/**
 * Stream chat use case — handles full SSE pipeline:
 * fetch → parse SSE data → call callbacks → done
 */
export const streamChatUseCase = {
  execute: async (
    sessionId: number,
    query: string,
    callbacks: StreamCallbacks
  ): Promise<void> => {
    try {
      const response = await chatService.streamChat(sessionId, query);

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }
      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ') || line.includes('[DONE]')) continue;

          try {
            const raw = line.replace('data: ', '').trim();
            if (!raw) continue;
            const obj = JSON.parse(raw);

            if (obj.content) {
              callbacks.onToken(obj.content);
            }
            if (obj.sources && obj.sources.length > 0) {
              callbacks.onSources(obj.sources);
            }
          } catch {
            // Partial JSON chunk — safe to ignore
          }
        }
      }

      callbacks.onDone();
    } catch (err) {
      callbacks.onError(err instanceof Error ? err : new Error(String(err)));
    }
  },
};
