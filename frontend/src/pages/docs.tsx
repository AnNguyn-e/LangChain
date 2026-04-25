import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Navbar } from '@/components/Navbar';
import { ToastContainer, createToastManager } from '@/components/Toast';
import {
  useDocumentList,
  useUploadDocuments,
  useDeleteDocument,
  useRestoreDocument,
} from '@/features/documents/hooks/useDocuments';
import { useTagList, useCreateTag, useAssignTag } from '@/features/documents/hooks/useTags';
import { DocumentGrid } from '@/features/documents/components/DocumentGrid';
import { TagSidebar } from '@/features/documents/components/TagSidebar';
import { UploadButton } from '@/features/documents/components/UploadButton';

export default function DocsPage() {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [selectedTag, setSelectedTag] = useState<number | null>(null);
  const [toasts, setToasts] = useState([] as any[]);
  const addToast = createToastManager(setToasts);

  const { data: documents = [], isLoading: docsLoading, refetch: refetchDocs } = useDocumentList(search, selectedTag ?? undefined);
  const { mutate: uploadMutate, isPending: uploading } = useUploadDocuments();
  const { mutate: deleteMutate } = useDeleteDocument();
  const { mutate: restoreMutate } = useRestoreDocument();
  const { data: tags = [], isLoading: tagsLoading } = useTagList();
  const { mutate: createTagMutate } = useCreateTag();
  const { mutate: assignTagMutate } = useAssignTag();

  const loading = docsLoading || tagsLoading;

  useEffect(() => {
    if (!localStorage.getItem('auth_token')) router.replace('/login');
  }, []);

  const handleUpload = (files: File[]) => {
    uploadMutate(files, {
      onSuccess: () => { addToast('Tải lên thành công', 'success'); refetchDocs(); },
      onError: (err:any) => addToast(err?.response?.data?.detail || 'Lỗi tải lên', 'error'),
    });
  };

  const handleDelete = (id: number) => {
    if (!confirm('Bạn có chắc muốn xóa tài liệu này?')) return;
    deleteMutate(id, { onSuccess: () => { addToast('Xóa thành công', 'success'); refetchDocs(); }, onError: () => addToast('Lỗi khi xóa', 'error') });
  };

  const handleRestore = (id: number) => {
    restoreMutate(id, { onSuccess: () => { addToast('Khôi phục thành công', 'success'); refetchDocs(); }, onError: () => addToast('Lỗi khôi phục', 'error') });
  };

  const handleCreateTag = () => {
    const name = prompt('Nhập tên tag mới:');
    if (!name) return;
    const color = prompt('Nhập mã màu (e.g., #3b82f6):', '#3b82f6') || '#3b82f6';
    createTagMutate({ name, color }, { onSuccess: () => addToast('Tag tạo thành công', 'success'), onError: () => addToast('Lỗi tạo tag', 'error') });
  };

  const handleAssignTag = (docId: number) => {
    const tagIdStr = prompt('Nhập ID tag muốn gắn (xem danh sách dưới):');
    if (!tagIdStr) return;
    const tagId = parseInt(tagIdStr);
    assignTagMutate({ docId, tagId }, { onSuccess: () => { addToast('Tag gắn thành công', 'success'); refetchDocs(); }, onError: () => addToast('Lỗi gắn tag', 'error') });
  };

  return (
    <>
      <Head>
        <title>DocAI | Quản lý tài liệu</title>
        <meta name="description" content="Quản lý tài liệu nội bộ với DocAI" />
      </Head>
      <Navbar onLogout={() => { localStorage.removeItem('auth_token'); router.push('/login'); }} />
      <ToastContainer toasts={toasts} />
      <div className="main-content">
        <TagSidebar search={search} onSearchChange={setSearch} tags={tags} selectedTag={selectedTag} onSelectTag={setSelectedTag} onCreateTag={handleCreateTag} isLoading={tagsLoading} />
        <section className="doc-section">
          <div className="doc-header">
            <h2>Tài liệu của tôi</h2>
            <UploadButton onUpload={handleUpload} uploading={uploading} />
          </div>
          <DocumentGrid documents={documents} isLoading={loading} onDelete={handleDelete} onRestore={handleRestore} onAssignTag={handleAssignTag} />
        </section>
      </div>
    </>
  );
}
