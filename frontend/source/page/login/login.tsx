import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import axios from 'axios';
import { saveToken, isLoggedIn } from '@/lib/auth';
import api from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ username?: string; password?: string }>({});
  const [apiError, setApiError] = useState('');
  const [loading, setLoading] = useState(false);
  const usernameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isLoggedIn()) {
      router.replace('/');
      return;
    }
    usernameRef.current?.focus();
  }, []);

  function validateForm(): boolean {
    const errs: { username?: string; password?: string } = {};
    if (!username.trim()) errs.username = 'Vui lòng nhập tên đăng nhập';
    if (!password) errs.password = 'Vui lòng nhập mật khẩu';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setApiError('');
    if (!validateForm()) return;
    setLoading(true);

    try {
      const params = new URLSearchParams();
      params.append('username', username.trim());
      params.append('password', password);

      const { data } = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/login`,
        params,
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );

      saveToken(data.access_token);
      router.push('/');
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setApiError(detail || 'Đăng nhập thất bại. Vui lòng thử lại.');
      } else {
        setApiError('Đã xảy ra lỗi. Kiểm tra kết nối máy chủ.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Head>
        <title>Đăng nhập – DocAI Local</title>
        <meta name="description" content="Đăng nhập vào hệ thống quản lý tài liệu nội bộ" />
      </Head>

      <div className="auth-page">
        <form className="auth-card" onSubmit={handleSubmit} noValidate>
          {/* Logo */}
          <div className="auth-logo">
            <div className="auth-logo-icon">📂</div>
            <span className="auth-logo-text">DocAI Local</span>
          </div>

          <h1 className="auth-title">Chào mừng trở lại</h1>
          <p className="auth-subtitle">Đăng nhập để tiếp tục quản lý tài liệu</p>

          {/* API error */}
          {apiError && (
            <div className="alert alert-error" role="alert">
              <span>⚠</span> {apiError}
            </div>
          )}

          {/* Username */}
          <div className="form-group">
            <label htmlFor="username" className="form-label">Tên đăng nhập</label>
            <input
              id="username"
              ref={usernameRef}
              className={`form-control${errors.username ? ' is-error' : ''}`}
              type="text"
              autoComplete="username"
              placeholder="Nhập tên đăng nhập"
              value={username}
              onChange={(e) => { setUsername(e.target.value); setErrors((p) => ({ ...p, username: undefined })); }}
            />
            {errors.username && <p className="form-error">⚑ {errors.username}</p>}
          </div>

          {/* Password */}
          <div className="form-group">
            <label htmlFor="password" className="form-label">Mật khẩu</label>
            <input
              id="password"
              className={`form-control${errors.password ? ' is-error' : ''}`}
              type="password"
              autoComplete="current-password"
              placeholder="Nhập mật khẩu"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setErrors((p) => ({ ...p, password: undefined })); }}
            />
            {errors.password && <p className="form-error">⚑ {errors.password}</p>}
          </div>

          <button className="btn-primary" type="submit" disabled={loading} id="login-submit">
            {loading ? 'Đang xét xử...' : 'Đăng nhập'}
          </button>

          <div className="auth-divider">
            Chưa có tài khoản?{' '}
            <Link href="/register">Đăng ký ngay</Link>
          </div>
        </form>
      </div>
    </>
  );
}
