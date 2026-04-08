import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import axios from 'axios';
import { saveToken, isLoggedIn } from '@/lib/auth';
import api from '@/lib/api';

interface FormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface FormErrors {
  username?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState<FormData>({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [apiError, setApiError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoggedIn()) router.replace('/');
  }, []);

  function update(field: keyof FormData) {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setForm((p) => ({ ...p, [field]: e.target.value }));
      setErrors((p) => ({ ...p, [field]: undefined }));
      setApiError('');
    };
  }

  function validateForm(): boolean {
    const errs: FormErrors = {};
    const usernamePattern = /^[a-zA-Z0-9_]+$/;
    const emailPattern = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

    if (!form.username.trim()) {
      errs.username = 'Vui lòng nhập tên đăng nhập';
    } else if (form.username.trim().length < 3) {
      errs.username = 'Username phải có ít nhất 3 ký tự';
    } else if (!usernamePattern.test(form.username.trim())) {
      errs.username = 'Username chỉ được chứa chữ cái, số và dấu gạch dưới';
    }

    if (form.email.trim() && !emailPattern.test(form.email.trim())) {
      errs.email = 'Email không hợp lệ';
    }

    if (!form.password) {
      errs.password = 'Vui lòng nhập mật khẩu';
    } else if (form.password.length < 6) {
      errs.password = 'Mật khẩu phải có ít nhất 6 ký tự';
    }

    if (!form.confirmPassword) {
      errs.confirmPassword = 'Vui lòng xác nhận mật khẩu';
    } else if (form.password !== form.confirmPassword) {
      errs.confirmPassword = 'Mật khẩu xác nhận không khớp';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setApiError('');
    setSuccessMsg('');
    if (!validateForm()) return;
    setLoading(true);

    try {
      // Step 1: Register
      await api.post('/auth/register', {
        username: form.username.trim(),
        email: form.email.trim() || undefined,
        password: form.password,
      });

      setSuccessMsg('Đăng ký thành công! Đang đăng nhập...');

      // Step 2: Auto-login
      const params = new URLSearchParams();
      params.append('username', form.username.trim());
      params.append('password', form.password);

      const { data } = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'}/auth/login`,
        params,
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );

      saveToken(data.access_token);
      setTimeout(() => router.push('/'), 800);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (typeof detail === 'string') {
          setApiError(detail);
        } else if (Array.isArray(detail)) {
          // Pydantic validation errors
          const msgs = detail.map((d: { msg: string }) => d.msg).join(', ');
          setApiError(msgs);
        } else {
          setApiError('Đăng ký thất bại. Vui lòng thử lại.');
        }
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
        <title>Đăng ký – DocAI Local</title>
        <meta name="description" content="Tạo tài khoản hệ thống quản lý tài liệu nội bộ" />
      </Head>

      <div className="auth-page">
        <form className="auth-card" onSubmit={handleSubmit} noValidate>
          {/* Logo */}
          <div className="auth-logo">
            <div className="auth-logo-icon">📂</div>
            <span className="auth-logo-text">DocAI Local</span>
          </div>

          <h1 className="auth-title">Tạo tài khoản</h1>
          <p className="auth-subtitle">Điền thông tin để bắt đầu sử dụng hệ thống</p>

          {apiError && (
            <div className="alert alert-error" role="alert">
              <span>⚠</span> {apiError}
            </div>
          )}
          {successMsg && (
            <div className="alert alert-success" role="status">
              <span>✓</span> {successMsg}
            </div>
          )}

          {/* Username */}
          <div className="form-group">
            <label htmlFor="reg-username" className="form-label">Tên đăng nhập *</label>
            <input
              id="reg-username"
              className={`form-control${errors.username ? ' is-error' : ''}`}
              type="text"
              autoComplete="username"
              placeholder="Ít nhất 3 ký tự, chỉ chữ/số/_"
              value={form.username}
              onChange={update('username')}
            />
            {errors.username && <p className="form-error">⚑ {errors.username}</p>}
          </div>

          {/* Email */}
          <div className="form-group">
            <label htmlFor="reg-email" className="form-label">Email (không bắt buộc)</label>
            <input
              id="reg-email"
              className={`form-control${errors.email ? ' is-error' : ''}`}
              type="email"
              autoComplete="email"
              placeholder="example@domain.com"
              value={form.email}
              onChange={update('email')}
            />
            {errors.email && <p className="form-error">⚑ {errors.email}</p>}
          </div>

          {/* Password */}
          <div className="form-group">
            <label htmlFor="reg-password" className="form-label">Mật khẩu *</label>
            <input
              id="reg-password"
              className={`form-control${errors.password ? ' is-error' : ''}`}
              type="password"
              autoComplete="new-password"
              placeholder="Ít nhất 6 ký tự"
              value={form.password}
              onChange={update('password')}
            />
            {errors.password && <p className="form-error">⚑ {errors.password}</p>}
          </div>

          {/* Confirm Password */}
          <div className="form-group">
            <label htmlFor="reg-confirm" className="form-label">Xác nhận mật khẩu *</label>
            <input
              id="reg-confirm"
              className={`form-control${errors.confirmPassword ? ' is-error' : ''}`}
              type="password"
              autoComplete="new-password"
              placeholder="Nhập lại mật khẩu"
              value={form.confirmPassword}
              onChange={update('confirmPassword')}
            />
            {errors.confirmPassword && <p className="form-error">⚑ {errors.confirmPassword}</p>}
          </div>

          <button className="btn-primary" type="submit" disabled={loading} id="register-submit">
            {loading ? 'Đang xử lý...' : 'Tạo tài khoản'}
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
