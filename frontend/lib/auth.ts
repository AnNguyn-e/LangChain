const TOKEN_KEY = 'auth_token';

export interface UserPayload {
  sub: string;      // username
  exp: number;
  iat?: number;
}

/** Decode JWT payload (base64url) – no verification, client-side only */
function decodePayload(token: string): UserPayload | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const payload = atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(payload) as UserPayload;
  } catch {
    return null;
  }
}

export function saveToken(token: string): void {
  if (typeof window !== 'undefined') localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function removeToken(): void {
  if (typeof window !== 'undefined') localStorage.removeItem(TOKEN_KEY);
}

export function isLoggedIn(): boolean {
  const token = getToken();
  if (!token) return false;
  const payload = decodePayload(token);
  if (!payload) return false;
  // Check expiry
  return payload.exp * 1000 > Date.now();
}

/** Returns the username stored inside the JWT */
export function getUsername(): string | null {
  const token = getToken();
  if (!token) return null;
  return decodePayload(token)?.sub ?? null;
}
