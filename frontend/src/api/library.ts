import { authHeaders } from "../auth/session";

export interface LibraryDocument {
  id: string;
  filename: string;
  space: string;
  media_type: string;
  extractor: string;
  embedding_kind: string;
  owner_id: string;
  owner_name: string;
  owner_email: string;
  shared: boolean;
  excerpt: string;
  created_at: string;
}

export interface LibraryExcerpt {
  chunk_index: number;
  content: string;
}

export interface LibraryAnswer {
  conversation_id: string;
  document_id: string;
  filename: string;
  status: string;
  answer: string | null;
  error_message: string | null;
  excerpts: LibraryExcerpt[];
}

export interface DocumentAccess {
  user_id: string;
  display_name: string;
  email: string;
  owner: boolean;
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";

async function errorMessage(response: Response, fallback: string): Promise<string> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return typeof body?.detail === "string" ? body.detail : fallback;
}

export async function loadLibrary(space?: string): Promise<LibraryDocument[]> {
  const query = space ? `?space=${encodeURIComponent(space)}` : "";
  const response = await fetch(`${apiBase}/api/v1/library${query}`, { headers: authHeaders() });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Documents could not be loaded"));
  }
  return (await response.json()) as LibraryDocument[];
}

export async function uploadLibraryFile(file: File, space?: string): Promise<LibraryDocument> {
  const body = new FormData();
  body.append("file", file);
  if (space) {
    body.append("space", space);
  }
  const response = await fetch(`${apiBase}/api/v1/library`, {
    method: "POST",
    headers: authHeaders(),
    body,
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "The file could not be read"));
  }
  return (await response.json()) as LibraryDocument;
}

export async function askLibrary(
  documentId: string,
  prompt: string,
  modelId: string,
  conversationId: string | null,
): Promise<LibraryAnswer> {
  const response = await fetch(`${apiBase}/api/v1/library/${documentId}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({
      prompt,
      model_id: modelId,
      conversation_id: conversationId,
    }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "The document chat failed"));
  }
  return (await response.json()) as LibraryAnswer;
}

export async function loadAdminLibrary(): Promise<LibraryDocument[]> {
  const response = await fetch(`${apiBase}/api/v1/admin/library`, { headers: authHeaders() });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Uploaded documents could not be loaded"));
  }
  return (await response.json()) as LibraryDocument[];
}

export async function loadDocumentAccess(documentId: string): Promise<DocumentAccess[]> {
  const response = await fetch(`${apiBase}/api/v1/admin/library/${documentId}/access`, {
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Access could not be loaded"));
  }
  return (await response.json()) as DocumentAccess[];
}

export async function grantDocumentAccess(documentId: string, userId: string): Promise<void> {
  const response = await fetch(`${apiBase}/api/v1/admin/library/${documentId}/access`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Access could not be granted"));
  }
}

export async function revokeDocumentAccess(documentId: string, userId: string): Promise<void> {
  const response = await fetch(`${apiBase}/api/v1/admin/library/${documentId}/access/${userId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Access could not be removed"));
  }
}
