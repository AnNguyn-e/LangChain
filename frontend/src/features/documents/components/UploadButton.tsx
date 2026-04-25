import React, { useRef } from 'react';

interface UploadButtonProps {
  onUpload: (files: File[]) => void;
  uploading: boolean;
}

export const UploadButton: React.FC<UploadButtonProps> = ({ onUpload, uploading }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (files.length > 0) {
      onUpload(files);
      // Reset so same file can be re-uploaded
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="upload-zone">
      <input
        type="file"
        multiple
        hidden
        ref={fileInputRef}
        onChange={handleChange}
        accept=".pdf,.docx,.txt"
        id="file-upload-input"
      />
      <button
        id="upload-btn"
        className="upload-btn"
        onClick={() => fileInputRef.current?.click()}
        disabled={uploading}
      >
        {uploading ? '⏳ Đang xử lý...' : '⬆ Tải lên (PDF/DOCX/TXT)'}
      </button>
    </div>
  );
};
