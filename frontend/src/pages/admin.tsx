import React from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import Navbar from '../components/Navbar';
import { useAuth } from '../features/auth';
import { useAdminUsers, UserTable } from '../features/admin';
import Toast, { useToast } from '../components/Toast';

export default function AdminPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();
  const { toast, showToast, hideToast } = useToast();
  
  const { users, isLoading: isUsersLoading, updateRole, updateStatus } = useAdminUsers();

  // Route guard
  React.useEffect(() => {
    if (!isAuthLoading && (!user || user.role !== 'ADMIN')) {
      router.push('/dashboard');
    }
  }, [user, isAuthLoading, router]);

  const handleUpdateRole = async (userId: number, newRole: 'USER' | 'MANAGER' | 'ADMIN') => {
    try {
      await updateRole({ userId, data: { role: newRole } });
      showToast('Cập nhật quyền thành công', 'success');
    } catch (error) {
      showToast('Lỗi khi cập nhật quyền', 'error');
    }
  };

  const handleUpdateStatus = async (userId: number, isActive: boolean) => {
    try {
      await updateStatus({ userId, data: { is_active: isActive } });
      showToast('Cập nhật trạng thái thành công', 'success');
    } catch (error) {
      showToast('Lỗi khi cập nhật trạng thái', 'error');
    }
  };

  if (isAuthLoading || !user || user.role !== 'ADMIN') {
    return <div className="min-h-screen flex items-center justify-center">Đang tải...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Head>
        <title>Quản trị | Enterprise DocAI</title>
      </Head>

      <Navbar />

      <main className="flex-grow container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Quản lý người dùng</h1>
          <p className="text-gray-600 mt-2">Dành riêng cho Quản trị viên hệ thống.</p>
        </div>

        {isUsersLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : users ? (
          <UserTable 
            users={users} 
            onUpdateRole={handleUpdateRole} 
            onUpdateStatus={handleUpdateStatus} 
          />
        ) : (
          <div className="bg-white p-6 rounded-lg shadow text-center text-gray-500">
            Không tìm thấy dữ liệu người dùng.
          </div>
        )}
      </main>

      {toast.isVisible && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={hideToast}
        />
      )}
    </div>
  );
}
