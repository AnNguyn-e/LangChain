import React from 'react';
import type { Document } from '../models/document';
import { formatFileSize } from '../hooks/useDocuments';

interface DocumentCardProps {
  doc: Document;
  onDelete: (id: number) => void;
  onRestore?: (id: number) => void;
  onAssignTag: (docId: number) => void;
}

const FILE_ICONS: Record<string, string> = {
  PDF: '📄',
  DOCX: '📝',
  TXT: '🗒️',
};

export const DocumentCard: React.FC<DocumentCardProps> = ({
  doc,
  onDelete,
  onRestore,
  onAssignTag,
}) => {
  const isDeleted = doc.is_deleted ?? false;

  return (
    <div className={`doc-card${isDeleted ? ' deleted' : ''}`}>
      <div className="doc-icon">{FILE_ICONS[doc.file_type ?? ''] ?? '📁'}</div>

      <div className="doc-info">
        <h4 title={doc.filename}>{doc.filename}</h4>

        <div className="doc-meta">
          <span>{formatFileSize(doc.file_size)}</span>
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <span className={`status-badge ${doc.status}`}>{doc.status}</span>
            {doc.visibility && (
              <span className={`visibility-badge ${doc.visibility}`}>
                {doc.visibility === 'public' ? '🌐' : '🔒'} {doc.visibility}
              </span>
            )}
          </div>
        </div>

        <div className="doc-tags">
          {doc.tags.map((t) => (
            <span
              key={t.id}
              className="tag-item"
              style={{ backgroundColor: t.color }}
              title={`#${t.name}`}
            />
          ))}
          {!isDeleted && (
            <button
              className="tag-plus"
              onClick={() => onAssignTag(doc.id)}
              title="Gắn tag"
            >
              +
            </button>
          )}
        </div>
      </div>

      <div className="doc-actions">
        {isDeleted && onRestore ? (
          <button className="restore-btn" onClick={() => onRestore(doc.id)}>
            ↩ Khôi phục
          </button>
        ) : (
          <button className="delete-btn" onClick={() => onDelete(doc.id)}>
            Xóa
          </button>
        )}
      </div>
    </div>
  );
};
