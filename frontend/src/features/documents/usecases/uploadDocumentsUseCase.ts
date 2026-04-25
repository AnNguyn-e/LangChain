// Application layer — upload validation + business logic

import { documentService } from '../services/documentService';

const ALLOWED_EXTENSIONS = /\.(pdf|docx|txt)$/i;
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB

export interface UploadValidationResult {
  validFiles: File[];
  rejectedCount: number;
}

/**
 * Validates files client-side before uploading
 */
function validateFiles(files: File[]): UploadValidationResult {
  const validFiles = files.filter(
    (f) => f.size <= MAX_FILE_SIZE && ALLOWED_EXTENSIONS.test(f.name)
  );
  return {
    validFiles,
    rejectedCount: files.length - validFiles.length,
  };
}

/**
 * Upload use case — validates then uploads
 */
export const uploadDocumentsUseCase = {
  validateFiles,

  execute: async (files: File[]) => {
    const { validFiles } = validateFiles(files);
    if (validFiles.length === 0) {
      throw new Error('Không có file hợp lệ để tải lên');
    }
    const res = await documentService.uploadMultiple(validFiles);
    return res.data;
  },
};
