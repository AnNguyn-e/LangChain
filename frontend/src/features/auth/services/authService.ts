// Infrastructure layer — only API calls, no business logic

import api from '@/lib/api';
import type { UserInfo, AuthToken, RegisterPayload } from '../models/user';

export const authService = {
  /**
   * Login with username/password (OAuth2 form)
   */
  login: (username: string, password: string): Promise<{ data: AuthToken }> => {
    const params = new URLSearchParams();
    params.append('username', username.trim());
    params.append('password', password);
    return api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },

  /**
   * Register a new user account
   */
  register: (payload: RegisterPayload): Promise<{ data: UserInfo }> => {
    return api.post('/auth/register', {
      username: payload.username.trim(),
      email: payload.email?.trim() || undefined,
      password: payload.password,
    });
  },

  /**
   * Get the current authenticated user
   */
  getMe: (): Promise<{ data: UserInfo }> => {
    return api.get('/auth/me');
  },
};
