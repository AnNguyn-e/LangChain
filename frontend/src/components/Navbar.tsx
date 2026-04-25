import React from 'react';
import { useRouter } from 'next/router';
import type { UserInfo } from '@/features/auth/models/user';

interface NavbarProps {
  user?: UserInfo;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onLogout }) => {
  const router = useRouter();

  return (
    <nav className="navbar">
      <div className="logo" onClick={() => router.push('/')}>
        DocAI
      </div>
      <div className="user-info" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {user && (
          <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
            👤 {user.username}
            {user.role !== 'USER' && (
              <span
                style={{
                  marginLeft: 8,
                  padding: '2px 8px',
                  borderRadius: 99,
                  fontSize: '0.7rem',
                  background: user.role === 'ADMIN' ? 'rgba(168,85,247,0.2)' : 'rgba(59,130,246,0.2)',
                  color: user.role === 'ADMIN' ? '#c084fc' : '#60a5fa',
                }}
              >
                {user.role}
              </span>
            )}
          </span>
        )}
        {user?.role === 'ADMIN' && (
          <button
            className="logout-btn"
            style={{ background: 'rgba(168,85,247,0.15)', color: '#c084fc', borderColor: 'rgba(168,85,247,0.3)' }}
            onClick={() => router.push('/admin')}
          >
            ⚙ Admin
          </button>
        )}
        <button id="logout-btn" className="logout-btn" onClick={onLogout}>
          Đăng xuất
        </button>
      </div>
    </nav>
  );
};
