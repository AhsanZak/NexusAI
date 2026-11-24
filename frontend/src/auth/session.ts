export interface SessionUser {
  id: string;
  email: string;
  display_name: string;
  role: string;
  created_at: string;
}

export interface Session {
  token: string;
  user: SessionUser;
}

const storageKey = "nexusai.session";

export function loadSession(): Session | null {
  const raw = localStorage.getItem(storageKey);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function saveSession(session: Session): void {
  localStorage.setItem(storageKey, JSON.stringify(session));
}

export function clearSession(): void {
  localStorage.removeItem(storageKey);
}

export function authHeaders(): HeadersInit {
  const session = loadSession();
  return session ? { Authorization: `Bearer ${session.token}` } : {};
}
