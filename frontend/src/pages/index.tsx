import { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { useCurrentUser, useLogout } from '@/features/auth/hooks/useAuth';
import { isLoggedIn } from '@/lib/auth';

export default function DashboardPage() {
  const router = useRouter();
  const { data: user, isLoading, isError } = useCurrentUser();
  const logout = useLogout();

  // ── Auth guard ──────────────────────────────────────────────
  useEffect(() => {
    if (typeof window !== 'undefined' && (!isLoggedIn() || isError)) {
      logout();
    }
  }, [isError]); // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading) {
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
        <meta name="description" content="Trang quản lý tài liệu AI nội bộ" />
      </Head>

      <div className="dashboard-page">
        {/* Header */}
        <header className="dashboard-header">
          <div className="dashboard-brand">
            <span>📂</span> DocAI Local
          </div>
          <div className="dashboard-user">
            <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              Xin chào, <strong style={{ color: 'var(--text-primary)' }}>{user.username}</strong>
            </span>
            <span className={`role-badge ${user.role.toLowerCase()}`}>{user.role}</span>
            {user.role === 'ADMIN' && (
              <button
                id="admin-btn"
                className="btn-logout"
                style={{ background: 'rgba(168,85,247,0.15)', color: '#c084fc', borderColor: 'rgba(168,85,247,0.3)' }}
                onClick={() => router.push('/admin')}
              >
                ⚙ Admin
              </button>
            )}
            <button id="logout-btn" className="btn-logout" onClick={logout}>
              Đăng xuất
            </button>
          </div>
        </header>

        {/* Main */}
        <main className="dashboard-content">
          <div className="welcome-card">
            <div className="welcome-avatar">{initials}</div>
            <h1>Chào mừng, {user.username}! 👋</h1>
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

            <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', marginTop: '2rem', flexWrap: 'wrap' }}>
              <button
                id="nav-docs-btn"
                className="btn-primary"
                onClick={() => router.push('/docs')}
                style={{ padding: '1rem 2rem', fontSize: '1.1rem', margin: 0 }}
              >
                📂 Quản lý tài liệu
              </button>
              <button
                id="nav-chat-btn"
                className="btn-primary"
                onClick={() => router.push('/chat')}
                style={{ padding: '1rem 2rem', fontSize: '1.1rem', margin: 0, background: 'linear-gradient(135deg, #10b981, #059669)' }}
              >
                💬 Chatbot AI
              </button>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
