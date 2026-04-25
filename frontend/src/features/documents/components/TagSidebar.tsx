import React from 'react';
import type { Tag } from '../models/document';

interface TagSidebarProps {
  search: string;
  onSearchChange: (value: string) => void;
  tags: Tag[];
  selectedTag: number | null;
  onSelectTag: (id: number | null) => void;
  onCreateTag: () => void;
  isLoading?: boolean;
}

export const TagSidebar: React.FC<TagSidebarProps> = ({
  search,
  onSearchChange,
  tags,
  selectedTag,
  onSelectTag,
  onCreateTag,
  isLoading,
}) => {
  return (
    <aside className="sidebar">
      <div className="section">
        <h3>Tìm kiếm</h3>
        <input
          id="doc-search"
          type="text"
          placeholder="Tên tài liệu..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="section">
        <div className="section-header">
          <h3>Thẻ (Tags)</h3>
          <button
            className="add-btn"
            onClick={onCreateTag}
            title="Tạo tag mới"
            id="create-tag-btn"
          >
            +
          </button>
        </div>

        <div className="tag-list">
          <button
            className={`tag-pill${selectedTag === null ? ' active' : ''}`}
            onClick={() => onSelectTag(null)}
          >
            Tất cả
          </button>

          {!isLoading && tags.map((tag) => (
            <button
              key={tag.id}
              className={`tag-pill${selectedTag === tag.id ? ' active' : ''}`}
              style={{ borderLeft: `3px solid ${tag.color}` }}
              onClick={() => onSelectTag(tag.id)}
            >
              #{tag.name}{' '}
              <span style={{ opacity: 0.5, fontSize: '0.75rem' }}>
                (ID: {tag.id})
              </span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
};
