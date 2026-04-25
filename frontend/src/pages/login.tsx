import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import { useLogin } from '@/features/auth/hooks/useAuth';
import { isLoggedIn } from '@/lib/auth';
import type { LoginFormErrors } from '@/features/auth/models/user';

export default function LoginPage() {
  const router = useRouter();
  const { loginAsync, isPending, validate } = useLogin();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<LoginFormErrors>({});
  const [apiError, setApiError] = useState('');
  const usernameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isLoggedIn()) { router.replace('/'); return; }
    usernameRef.current?.focus();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setApiError('');
    const formErrors = validate({ username, password });
    if (Object.keys(formErrors).length > 0) { setErrors(formErrors); return; }

    const result = await loginAsync({ username, password });
    if (!result.success) setApiError(result.error ?? 'Đăng nhập thất bại');
  }

  return (
    <>
      <Head>
        <title>Đăng nhập – DocAI Local</title>
        <meta name="description" content="Đăng nhập vào hệ thống quản lý tài liệu nội bộ" />
      </Head>

      <div className="auth-page">
        <form className="auth-card" onSubmit={handleSubmit} noValidate>
          <div className="auth-logo">
            <div className="auth-logo-icon">📂</div>
            <span className="auth-logo-text">DocAI Local</span>
          </div>

          <h1 className="auth-title">Chào mừng trở lại</h1>
          <p className="auth-subtitle">Đăng nhập để tiếp tục quản lý tài liệu</p>

          {apiError && (
            <div className="alert alert-error" role="alert">
              <span>⚠</span> {apiError}
            </div>
          )}

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

          <button className="btn-primary" type="submit" disabled={isPending} id="login-submit">
            {isPending ? 'Đang xử lý...' : 'Đăng nhập'}
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
