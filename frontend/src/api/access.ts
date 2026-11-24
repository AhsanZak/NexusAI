import { authHeaders } from "../auth/session";

export interface FeatureAccess {
  object_id: string;
  name: string;
  allowed: boolean;
}

export interface DocumentAccess {
  object_id: string;
  object_name: string;
  relation: string;
  actor: "member" | "super_admin";
  allowed: boolean;
  guest_allowed: boolean;
  content: string | null;
}

export interface Assignment {
  relation: string;
  object_id: string;
  object_name: string;
  object_type: string;
  actor: "member" | "guest";
}

export interface MyAccess {
  actor: "member" | "super_admin";
  subject: string;
  display_name: string;
  email: string;
  role: string;
  features: FeatureAccess[];
  documents: DocumentAccess[];
  assignments: Assignment[];
  guest_assignments: Assignment[];
}

export interface CatalogItem {
  object_id: string;
  name: string;
  object_type: string;
  releasing_relation: string;
  relations: string[];
}

export interface PermissionGrant {
  id: string;
  subject: string;
  actor: "member" | "guest";
  user_id: string | null;
  display_name: string;
  email: string | null;
  relation: string;
  object_id: string;
  object_name: string;
  object_type: string;
  created_at: string;
}

export interface PermissionList {
  catalog: CatalogItem[];
  grants: PermissionGrant[];
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";

async function errorMessage(response: Response, fallback: string): Promise<string> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return typeof body?.detail === "string" ? body.detail : fallback;
}

export async function loadMyAccess(): Promise<MyAccess> {
  const response = await fetch(`${apiBase}/api/v1/access/me`, { headers: authHeaders() });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Access could not be checked"));
  }
  return (await response.json()) as MyAccess;
}

export async function loadPermissions(): Promise<PermissionList> {
  const response = await fetch(`${apiBase}/api/v1/admin/permissions`, { headers: authHeaders() });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Permissions could not be loaded"));
  }
  return (await response.json()) as PermissionList;
}

export async function createPermission(input: {
  subject_kind: "member" | "guest";
  user_id?: string;
  relation: string;
  object_id: string;
}): Promise<PermissionGrant> {
  const response = await fetch(`${apiBase}/api/v1/admin/permissions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Could not grant that permission"));
  }
  return (await response.json()) as PermissionGrant;
}

export async function updatePermission(id: string, relation: string): Promise<PermissionGrant> {
  const response = await fetch(`${apiBase}/api/v1/admin/permissions/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ relation }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Could not update that permission"));
  }
  return (await response.json()) as PermissionGrant;
}

export async function deletePermission(id: string): Promise<void> {
  const response = await fetch(`${apiBase}/api/v1/admin/permissions/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Could not remove that permission"));
  }
}

export function featureAllowed(access: MyAccess | null, objectId: string, admin: boolean): boolean {
  if (admin) {
    return true;
  }
  return Boolean(access?.features.some((item) => item.object_id === objectId && item.allowed));
}
