// Controller layer — session hooks

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { chatService } from '../services/chatService';
import { chatHistoryUseCase } from '../usecases/chatHistoryUseCase';
import { isLoggedIn } from '@/lib/auth';
import type { ChatMessage } from '../models/chat';

export function useChatSessions() {
  return useQuery({
    queryKey: ['chat', 'sessions'],
    queryFn: async () => {
      const res = await chatService.getSessions();
      return res.data;
    },
    enabled: typeof window !== 'undefined' && isLoggedIn(),
  });
}

export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (title: string) => chatService.createSession(title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] });
    },
  });
}

export function useSessionMessages(
  sessionId: number | null,
  onMessages: (messages: ChatMessage[]) => void
) {
  const { data } = useQuery({
    queryKey: ['chat', 'messages', sessionId],
    queryFn: async () => {
      const res = await chatService.getMessages(sessionId!);
      return chatHistoryUseCase.mapMessages(res.data);
    },
    enabled: !!sessionId,
  });

  useEffect(() => {
    if (data) onMessages(data);
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps
}
