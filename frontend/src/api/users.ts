import { authHeaders, type SessionUser } from "../auth/session";

export interface LoginResult {
  access_token: string;
  user: SessionUser;
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";

async function errorMessage(response: Response, fallback: string): Promise<string> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return body?.detail || fallback;
}

export async function login(email: string, password: string): Promise<LoginResult> {
  const response = await fetch(`${apiBase}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Login failed"));
  }
  return (await response.json()) as LoginResult;
}

export async function loadMe(): Promise<SessionUser> {
  const response = await fetch(`${apiBase}/api/v1/auth/me`, { headers: authHeaders() });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Session expired"));
  }
  return (await response.json()) as SessionUser;
}

export async function loadUsers(): Promise<SessionUser[]> {
  const response = await fetch(`${apiBase}/api/v1/admin/users`, { headers: authHeaders() });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Could not load users"));
  }
  return (await response.json()) as SessionUser[];
}

export async function createUser(input: {
  email: string;
  display_name: string;
  password: string;
}): Promise<SessionUser> {
  const response = await fetch(`${apiBase}/api/v1/admin/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ ...input, role: "member" }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Could not add the user"));
  }
  return (await response.json()) as SessionUser;
}
