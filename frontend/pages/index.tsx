import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { isLoggedIn, getUsername, removeToken } from '@/lib/auth';
import api from '@/lib/api';

interface UserInfo {
  id: number;
  username: string;
  email: string | null;
  role: 'ADMIN' | 'USER';
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace('/login');
      return;
    }

    api.get<UserInfo>('/auth/me')
      .then(({ data }) => setUser(data))
      .catch(() => {
        // Token invalid or expired
        removeToken();
        router.replace('/login');
      })
      .finally(() => setLoading(false));
  }, []);

  function handleLogout() {
    removeToken();
    router.push('/login');
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: 15 }}>Đang tải...</span>
      </div>
    );
  }

  if (!user) return null;

  const initials = user.username.charAt(0).toUpperCase();

  return (
    <>
      <Head>
        <title>Dashboard – DocAI Local</title>
        <meta name="description" content="Trang quản lý tài liệu nội bộ" />
      </Head>

      <div className="dashboard-page">
        {/* Header */}
        <header className="dashboard-header">
          <div className="dashboard-brand">
            <span>📂</span>
            DocAI Local
          </div>
          <div className="dashboard-user">
            <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              Xin chào, <strong style={{ color: 'var(--text-primary)' }}>{user.username}</strong>
            </span>
            <span className={`role-badge ${user.role.toLowerCase()}`}>{user.role}</span>
            <button className="btn-logout" onClick={handleLogout} id="logout-btn">
              Đăng xuất
            </button>
          </div>
        </header>

        {/* Main content */}
        <main className="dashboard-content">
          <div className="welcome-card">
            <div className="welcome-avatar">{initials}</div>
            <h2>Chào mừng, {user.username}! 👋</h2>
            <p>Bạn đã đăng nhập thành công vào hệ thống quản lý tài liệu nội bộ.</p>

            <div className="info-grid">
              <div className="info-chip">
                <div className="info-chip-label">User ID</div>
                <div className="info-chip-value">#{user.id}</div>
              </div>
              <div className="info-chip">
                <div className="info-chip-label">Vai trò</div>
                <div className="info-chip-value">{user.role === 'ADMIN' ? '👑 Admin' : '👤 User'}</div>
              </div>
              <div className="info-chip">
                <div className="info-chip-label">Email</div>
                <div className="info-chip-value" style={{ fontSize: 14 }}>
                  {user.email || <span style={{ color: 'var(--text-muted)' }}>Chưa cập nhật</span>}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
