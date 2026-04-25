import React from 'react';
import Head from 'next/head';
import Navbar from '../components/Navbar';
import { useAuth } from '../features/auth';
import { useDashboardStats, StatsCard, ActivityFeed } from '../features/dashboard';

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: stats, isLoading, error } = useDashboardStats();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Head>
        <title>Dashboard | Enterprise DocAI</title>
      </Head>

      <Navbar />

      <main className="flex-grow container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-2">Xin chào, {user?.username}! Đây là tổng quan hệ thống.</p>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="bg-red-50 text-red-600 p-4 rounded-md">
            Lỗi khi tải dữ liệu thống kê: {error.message}
          </div>
        ) : stats ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatsCard 
                title="Người dùng" 
                value={stats.total_users} 
                colorClass="bg-gradient-to-br from-blue-500 to-blue-600" 
              />
              <StatsCard 
                title="Tài liệu" 
                value={stats.total_documents} 
                colorClass="bg-gradient-to-br from-indigo-500 to-indigo-600" 
              />
              <StatsCard 
                title="Dung lượng (MB)" 
                value={stats.total_storage_mb} 
                colorClass="bg-gradient-to-br from-emerald-500 to-emerald-600" 
              />
              <StatsCard 
                title="Cuộc hội thoại" 
                value={stats.total_chats} 
                colorClass="bg-gradient-to-br from-purple-500 to-purple-600" 
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <ActivityFeed documents={stats.recent_documents} />
              </div>
              <div>
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">Hành động nhanh</h3>
                  <div className="space-y-3">
                    <a href="/docs" className="block w-full text-center bg-blue-50 text-blue-600 hover:bg-blue-100 py-2 rounded-md transition-colors">
                      Tải lên tài liệu mới
                    </a>
                    <a href="/chat" className="block w-full text-center bg-purple-50 text-purple-600 hover:bg-purple-100 py-2 rounded-md transition-colors">
                      Bắt đầu chat
                    </a>
                    {user?.role === 'ADMIN' && (
                      <a href="/admin" className="block w-full text-center bg-red-50 text-red-600 hover:bg-red-100 py-2 rounded-md transition-colors">
                        Quản lý người dùng
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : null}
      </main>
    </div>
  );
}
