// Controller layer — tag hooks

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentService } from '../services/documentService';
import { tagUseCases } from '../usecases/tagUseCases';
import type { TagCreate } from '../models/document';

export function useTagList() {
  return useQuery({
    queryKey: ['tags'],
    queryFn: async () => {
      const res = await documentService.getTags();
      return res.data;
    },
  });
}

export function useCreateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: TagCreate) => tagUseCases.createTag(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] });
    },
  });
}

export function useAssignTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ docId, tagId }: { docId: number; tagId: number }) =>
      tagUseCases.assignTag(docId, tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

export function useRemoveTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ docId, tagId }: { docId: number; tagId: number }) =>
      tagUseCases.removeTag(docId, tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}
