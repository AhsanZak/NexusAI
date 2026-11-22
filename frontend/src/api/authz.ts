export interface AccessDecision {
  user_id: string;
  display_name: string;
  role: string;
  relation: string;
  object_id: string;
  object_name: string;
  shared: boolean;
  allowed: boolean;
  content: string | null;
}

export interface AuthzDemo {
  store_id: string;
  authorization_model_id: string;
  api_url: string;
  decisions: AccessDecision[];
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";

export async function loadAuthorizationDemo(): Promise<AuthzDemo> {
  const response = await fetch(`${apiBase}/api/v1/authz/demo`);
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail || `Authorization demo returned ${response.status}`);
  }
  return (await response.json()) as AuthzDemo;
}
