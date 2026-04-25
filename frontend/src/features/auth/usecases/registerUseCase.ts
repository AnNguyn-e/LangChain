// Application layer — register business logic

import type { RegisterFormErrors, RegisterPayload } from '../models/user';
import { authService } from '../services/authService';
import { saveToken } from '@/lib/auth';

interface RegisterResult {
  success: boolean;
  error?: string;
}

const USERNAME_PATTERN = /^[a-zA-Z0-9_]+$/;
const EMAIL_PATTERN = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

/**
 * Validates register form fields
 */
function validate(payload: RegisterPayload & { confirmPassword: string }): RegisterFormErrors {
  const errors: RegisterFormErrors = {};

  if (!payload.username.trim()) {
    errors.username = 'Vui lòng nhập tên đăng nhập';
  } else if (payload.username.trim().length < 3) {
    errors.username = 'Username phải có ít nhất 3 ký tự';
  } else if (!USERNAME_PATTERN.test(payload.username.trim())) {
    errors.username = 'Username chỉ được chứa chữ cái, số và dấu gạch dưới';
  }

  if (payload.email?.trim() && !EMAIL_PATTERN.test(payload.email.trim())) {
    errors.email = 'Email không hợp lệ';
  }

  if (!payload.password) {
    errors.password = 'Vui lòng nhập mật khẩu';
  } else if (payload.password.length < 6) {
    errors.password = 'Mật khẩu phải có ít nhất 6 ký tự';
  }

  if (!payload.confirmPassword) {
    errors.confirmPassword = 'Vui lòng xác nhận mật khẩu';
  } else if (payload.password !== payload.confirmPassword) {
    errors.confirmPassword = 'Mật khẩu xác nhận không khớp';
  }

  return errors;
}

/**
 * Register use case — validates, registers, then auto-logins
 */
export const registerUseCase = {
  validate,

  execute: async (
    payload: RegisterPayload & { confirmPassword: string }
  ): Promise<RegisterResult> => {
    try {
      // Step 1: Register
      await authService.register(payload);

      // Step 2: Auto login
      const loginRes = await authService.login(payload.username, payload.password);
      saveToken(loginRes.data.access_token);

      return { success: true };
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { data?: { detail?: string | Array<{ msg: string }> } };
      };
      const detail = axiosErr.response?.data?.detail;
      if (typeof detail === 'string') {
        return { success: false, error: detail };
      } else if (Array.isArray(detail)) {
        return { success: false, error: detail.map((d) => d.msg).join(', ') };
      }
      return { success: false, error: 'Đăng ký thất bại. Vui lòng thử lại.' };
    }
  },
};
