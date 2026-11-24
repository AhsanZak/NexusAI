import { authHeaders } from "../auth/session";

export interface KnowledgeSpace {
  id: string;
  label: string;
  summary: string;
  placeholder: string;
  extensions: string[];
  document_count: number;
  conversation_count: number;
}

export interface KnowledgeConversation {
  id: string;
  title: string;
  space: string | null;
  space_label: string;
  document_id: string | null;
  filename: string | null;
  intent_label: string | null;
  updated_at: string;
}

export interface KnowledgeHome {
  spaces: KnowledgeSpace[];
  conversations: KnowledgeConversation[];
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";

export async function loadKnowledgeHome(): Promise<KnowledgeHome> {
  const response = await fetch(`${apiBase}/api/v1/knowledge`, { headers: authHeaders() });
  if (!response.ok) {
    throw new Error("Knowledge spaces could not be loaded");
  }
  return (await response.json()) as KnowledgeHome;
}
