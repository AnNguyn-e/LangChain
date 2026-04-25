// Application layer — login business logic

import type { LoginFormErrors, LoginPayload } from '../models/user';
import { authService } from '../services/authService';
import { saveToken } from '@/lib/auth';

interface LoginResult {
  success: boolean;
  error?: string;
}

/**
 * Validates login form fields
 */
function validate(payload: LoginPayload): LoginFormErrors {
  const errors: LoginFormErrors = {};
  if (!payload.username.trim()) errors.username = 'Vui lòng nhập tên đăng nhập';
  if (!payload.password) errors.password = 'Vui lòng nhập mật khẩu';
  return errors;
}

/**
 * Login use case — validates, calls service, saves token
 */
export const loginUseCase = {
  validate,

  execute: async (payload: LoginPayload): Promise<LoginResult> => {
    try {
      const res = await authService.login(payload.username, payload.password);
      saveToken(res.data.access_token);
      return { success: true };
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const detail = axiosErr.response?.data?.detail;
      return {
        success: false,
        error: detail || 'Đăng nhập thất bại. Vui lòng thử lại.',
      };
    }
  },
};
