import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import { useRegister } from '@/features/auth/hooks/useAuth';
import { isLoggedIn } from '@/lib/auth';
import type { RegisterFormErrors } from '@/features/auth/models/user';

interface FormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export default function RegisterPage() {
  const router = useRouter();
  const { registerAsync, isPending, validate } = useRegister();

  const [form, setForm] = useState<FormData>({ username: '', email: '', password: '', confirmPassword: '' });
  const [errors, setErrors] = useState<RegisterFormErrors>({});
  const [apiError, setApiError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    if (isLoggedIn()) router.replace('/');
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function update(field: keyof FormData) {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setForm((p) => ({ ...p, [field]: e.target.value }));
      setErrors((p) => ({ ...p, [field]: undefined }));
      setApiError('');
    };
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setApiError('');
    setSuccessMsg('');
    const formErrors = validate(form);
    if (Object.keys(formErrors).length > 0) { setErrors(formErrors); return; }

    const result = await registerAsync(form);
    if (result.success) {
      setSuccessMsg('Đăng ký thành công! Đang đăng nhập...');
    } else {
      setApiError(result.error ?? 'Đăng ký thất bại');
    }
  }

  return (
    <>
      <Head>
        <title>Đăng ký – DocAI Local</title>
        <meta name="description" content="Tạo tài khoản hệ thống quản lý tài liệu nội bộ" />
      </Head>

      <div className="auth-page">
        <form className="auth-card" onSubmit={handleSubmit} noValidate>
          <div className="auth-logo">
            <div className="auth-logo-icon">📂</div>
            <span className="auth-logo-text">DocAI Local</span>
          </div>

          <h1 className="auth-title">Tạo tài khoản</h1>
          <p className="auth-subtitle">Điền thông tin để bắt đầu sử dụng hệ thống</p>

          {apiError && <div className="alert alert-error" role="alert"><span>⚠</span> {apiError}</div>}
          {successMsg && <div className="alert alert-success" role="status"><span>✓</span> {successMsg}</div>}

          <div className="form-group">
            <label htmlFor="reg-username" className="form-label">Tên đăng nhập *</label>
            <input id="reg-username" className={`form-control${errors.username ? ' is-error' : ''}`}
              type="text" autoComplete="username" placeholder="Ít nhất 3 ký tự, chỉ chữ/số/_"
              value={form.username} onChange={update('username')} />
            {errors.username && <p className="form-error">⚑ {errors.username}</p>}
          </div>

          <div className="form-group">
            <label htmlFor="reg-email" className="form-label">Email (không bắt buộc)</label>
            <input id="reg-email" className={`form-control${errors.email ? ' is-error' : ''}`}
              type="email" autoComplete="email" placeholder="example@domain.com"
              value={form.email} onChange={update('email')} />
            {errors.email && <p className="form-error">⚑ {errors.email}</p>}
          </div>

          <div className="form-group">
            <label htmlFor="reg-password" className="form-label">Mật khẩu *</label>
            <input id="reg-password" className={`form-control${errors.password ? ' is-error' : ''}`}
              type="password" autoComplete="new-password" placeholder="Ít nhất 6 ký tự"
              value={form.password} onChange={update('password')} />
            {errors.password && <p className="form-error">⚑ {errors.password}</p>}
          </div>

          <div className="form-group">
            <label htmlFor="reg-confirm" className="form-label">Xác nhận mật khẩu *</label>
            <input id="reg-confirm" className={`form-control${errors.confirmPassword ? ' is-error' : ''}`}
              type="password" autoComplete="new-password" placeholder="Nhập lại mật khẩu"
              value={form.confirmPassword} onChange={update('confirmPassword')} />
            {errors.confirmPassword && <p className="form-error">⚑ {errors.confirmPassword}</p>}
          </div>

          <button className="btn-primary" type="submit" disabled={isPending} id="register-submit">
            {isPending ? 'Đang xử lý...' : 'Tạo tài khoản'}
          </button>

          <div className="auth-divider">
            Đã có tài khoản?{' '}
            <Link href="/login">Đăng nhập</Link>
          </div>
        </form>
      </div>
    </>
  );
}
