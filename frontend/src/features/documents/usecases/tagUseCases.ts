// Application layer — tag use cases

import { documentService } from '../services/documentService';
import type { TagCreate } from '../models/document';

export const tagUseCases = {
  createTag: async (payload: TagCreate) => {
    const res = await documentService.createTag(payload);
    return res.data;
  },

  assignTag: async (docId: number, tagId: number): Promise<void> => {
    await documentService.assignTag(docId, tagId);
  },

  removeTag: async (docId: number, tagId: number): Promise<void> => {
    await documentService.removeTag(docId, tagId);
  },
};
