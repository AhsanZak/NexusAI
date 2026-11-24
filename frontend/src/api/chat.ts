import { authHeaders } from "../auth/session";

export interface ChatModelOption {
  id: string;
  name: string;
  state: "up" | "down";
  detail: string;
}

export interface ChatModelList {
  selected: string;
  models: ChatModelOption[];
}

export interface ChatTurn {
  id: string;
  role: string;
  content: string;
  model_name: string;
  intent: string | null;
  intent_label: string | null;
  created_at: string;
}

export interface ChatConversation {
  id: string;
  title: string;
  document_id: string | null;
  intent: string | null;
  intent_label: string | null;
  updated_at: string;
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";

async function errorMessage(response: Response, fallback: string): Promise<string> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return typeof body?.detail === "string" ? body.detail : fallback;
}

export async function loadChatModels(): Promise<ChatModelList> {
  const response = await fetch(`${apiBase}/api/v1/chat/models`, { headers: authHeaders() });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Models could not be loaded"));
  }
  return (await response.json()) as ChatModelList;
}

export async function saveChatModel(modelId: string): Promise<ChatModelList> {
  const response = await fetch(`${apiBase}/api/v1/chat/model`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ model_id: modelId }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "The model could not be changed"));
  }
  return (await response.json()) as ChatModelList;
}

export async function loadConversations(documentId?: string): Promise<ChatConversation[]> {
  const query = documentId ? `?document_id=${encodeURIComponent(documentId)}` : "";
  const response = await fetch(`${apiBase}/api/v1/chat/conversations${query}`, {
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Chats could not be loaded"));
  }
  return (await response.json()) as ChatConversation[];
}

export async function deleteConversation(conversationId: string): Promise<void> {
  const response = await fetch(`${apiBase}/api/v1/chat/conversations/${conversationId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "That chat could not be deleted"));
  }
}

export async function loadChatHistory(conversationId: string): Promise<ChatTurn[]> {
  const query = `?conversation_id=${encodeURIComponent(conversationId)}`;
  const response = await fetch(`${apiBase}/api/v1/chat/history${query}`, { headers: authHeaders() });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "Chat history could not be loaded"));
  }
  return (await response.json()) as ChatTurn[];
}
