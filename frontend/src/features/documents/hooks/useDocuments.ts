// Controller layer — document hooks

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentService } from '../services/documentService';
import { uploadDocumentsUseCase } from '../usecases/uploadDocumentsUseCase';
import { deleteDocumentUseCase } from '../usecases/deleteDocumentUseCase';

export function useDocumentList(search?: string, tagId?: number | null) {
  return useQuery({
    queryKey: ['documents', search, tagId],
    queryFn: async () => {
      const res = await documentService.list(search, tagId ?? undefined);
      return res.data;
    },
  });
}

export function useUploadDocuments() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (files: File[]) => uploadDocumentsUseCase.execute(files),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteDocumentUseCase.execute(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

export function useRestoreDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteDocumentUseCase.restore(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

/** Helper to format file size */
export function formatFileSize(bytes?: number): string {
  if (!bytes) return '0 KB';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}
