import React from 'react';
import type { Document } from '../models/document';
import { DocumentCard } from './DocumentCard';

interface DocumentGridProps {
  documents: Document[];
  isLoading: boolean;
  onDelete: (id: number) => void;
  onRestore?: (id: number) => void;
  onAssignTag: (docId: number) => void;
}

export const DocumentGrid: React.FC<DocumentGridProps> = ({
  documents,
  isLoading,
  onDelete,
  onRestore,
  onAssignTag,
}) => {
  if (isLoading) {
    return (
      <div className="doc-grid">
        <div className="loading">⏳ Đang tải...</div>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="doc-grid">
        <div className="empty">
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
          <p>Không tìm thấy tài liệu nào</p>
        </div>
      </div>
    );
  }

  return (
    <div className="doc-grid">
      {documents.map((doc) => (
        <DocumentCard
          key={doc.id}
          doc={doc}
          onDelete={onDelete}
          onRestore={onRestore}
          onAssignTag={onAssignTag}
        />
      ))}
    </div>
  );
};
