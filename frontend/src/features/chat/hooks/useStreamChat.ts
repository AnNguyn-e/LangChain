// Controller layer — streaming chat hook

import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { chatService } from '../services/chatService';
import { streamChatUseCase } from '../usecases/streamChatUseCase';
import type { ChatMessage } from '../models/chat';

interface UseStreamChatOptions {
  onError?: (msg: string) => void;
}

export function useStreamChat(options?: UseStreamChatOptions) {
  const [isGenerating, setIsGenerating] = useState(false);
  const queryClient = useQueryClient();

  const sendMessage = useCallback(
    async (
      query: string,
      sessionId: number | null,
      setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>,
      onSessionCreated?: (id: number) => void
    ) => {
      if (!query.trim() || isGenerating) return;

      let currentSessionId = sessionId;

      // Auto-create session if none exists
      if (!currentSessionId) {
        try {
          const res = await chatService.createSession(query.substring(0, 40));
          currentSessionId = res.data.id;
          queryClient.setQueryData(
            ['chat', 'sessions'],
            (prev: typeof res.data[] | undefined) => [res.data, ...(prev ?? [])]
          );
          onSessionCreated?.(currentSessionId);
        } catch {
          options?.onError?.('Không thể kết nối máy chủ');
          return;
        }
      }

      // Optimistically add user + placeholder AI message
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: query },
        { role: 'ai', content: '' },
      ]);
      setIsGenerating(true);

      await streamChatUseCase.execute(currentSessionId, query, {
        onToken: (token) => {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last?.role === 'ai') {
              next[next.length - 1] = { ...last, content: last.content + token };
            }
            return next;
          });
        },
        onSources: (sources) => {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last?.role === 'ai') {
              next[next.length - 1] = { ...last, sources };
            }
            return next;
          });
        },
        onDone: () => setIsGenerating(false),
        onError: () => {
          options?.onError?.('Đã có lỗi khi nhận phản hồi từ AI');
          setIsGenerating(false);
        },
      });
    },
    [isGenerating, queryClient, options]
  );

  return { sendMessage, isGenerating };
}
