// Infrastructure layer — only API calls, no business logic

import api from '@/lib/api';
import type { Document, Tag, UploadResult, TagCreate } from '../models/document';

export const documentService = {
  list: (search?: string, tagId?: number): Promise<{ data: Document[] }> =>
    api.get('/documents', { params: { search, tag_id: tagId } }),

  uploadMultiple: (files: File[]): Promise<{ data: UploadResult }> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    return api.post('/documents/upload-multiple', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  delete: (id: number): Promise<void> => api.delete(`/documents/${id}`),

  restore: (id: number): Promise<{ data: Document }> =>
    api.post(`/documents/${id}/restore`),

  getTags: (): Promise<{ data: Tag[] }> => api.get('/documents/tags'),

  createTag: (tag: TagCreate): Promise<{ data: Tag }> =>
    api.post('/documents/tags', tag),

  assignTag: (docId: number, tagId: number): Promise<void> =>
    api.post(`/documents/${docId}/tags/${tagId}`),

  removeTag: (docId: number, tagId: number): Promise<void> =>
    api.delete(`/documents/${docId}/tags/${tagId}`),
};
