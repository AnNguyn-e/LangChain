// Controller layer — connects UI to use cases

import { useMutation, useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/router';
import { authService } from '../services/authService';
import { loginUseCase } from '../usecases/loginUseCase';
import { registerUseCase } from '../usecases/registerUseCase';
import { removeToken, isLoggedIn } from '@/lib/auth';
import type { LoginPayload, RegisterPayload } from '../models/user';

/**
 * Hook to get the current authenticated user
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const res = await authService.getMe();
      return res.data;
    },
    enabled: typeof window !== 'undefined' && isLoggedIn(),
    retry: false,
  });
}

/**
 * Hook for login form
 */
export function useLogin() {
  const router = useRouter();

  const mutation = useMutation({
    mutationFn: (payload: LoginPayload) => loginUseCase.execute(payload),
    onSuccess: (result) => {
      if (result.success) {
        router.push('/');
      }
    },
  });

  return {
    login: mutation.mutate,
    loginAsync: mutation.mutateAsync,
    isPending: mutation.isPending,
    validate: loginUseCase.validate,
  };
}

/**
 * Hook for register form
 */
export function useRegister() {
  const router = useRouter();

  const mutation = useMutation({
    mutationFn: (payload: RegisterPayload & { confirmPassword: string }) =>
      registerUseCase.execute(payload),
    onSuccess: (result) => {
      if (result.success) {
        setTimeout(() => router.push('/'), 800);
      }
    },
  });

  return {
    register: mutation.mutate,
    registerAsync: mutation.mutateAsync,
    isPending: mutation.isPending,
    validate: registerUseCase.validate,
  };
}

/**
 * Hook for logout
 */
export function useLogout() {
  const router = useRouter();

  return () => {
    removeToken();
    router.push('/login');
  };
}
