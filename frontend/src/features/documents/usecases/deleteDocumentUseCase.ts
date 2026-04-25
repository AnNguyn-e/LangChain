// Application layer — delete document use case

import { documentService } from '../services/documentService';

export const deleteDocumentUseCase = {
  execute: async (id: number): Promise<void> => {
    await documentService.delete(id);
  },

  restore: async (id: number) => {
    const res = await documentService.restore(id);
    return res.data;
  },
};
