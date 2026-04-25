// Domain models for auth feature

export interface UserInfo {
  id: number;
  username: string;
  email: string | null;
  role: 'ADMIN' | 'MANAGER' | 'USER';
  department?: string | null;
  is_active?: boolean;
  created_at?: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email?: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface LoginFormErrors {
  username?: string;
  password?: string;
}

export interface RegisterFormErrors {
  username?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}
