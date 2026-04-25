// Domain models for documents feature

export interface Tag {
  id: number;
  name: string;
  color: string;
}

export type DocumentStatus = 'processing' | 'completed' | 'failed';
export type DocumentVisibility = 'private' | 'public';

export interface Document {
  id: number;
  filename: string;
  file_size?: number;
  file_type?: string;
  status: DocumentStatus;
  chunk_count: number;
  created_at: string;
  tags: Tag[];
  visibility?: DocumentVisibility;
  is_deleted?: boolean;
}

export interface UploadError {
  filename: string;
  error: string;
}

export interface UploadResult {
  results: Document[];
  errors: UploadError[];
}

export interface TagCreate {
  name: string;
  color: string;
}
