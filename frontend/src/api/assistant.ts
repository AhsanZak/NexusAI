import { authHeaders } from "../auth/session";
import type { AccessDecision } from "./authz";

export interface AssistantAnswer {
  conversation_id: string;
  user_id: string;
  display_name: string;
  role: string;
  status: string;
  answer: string | null;
  error_message: string | null;
  intent: string;
  intent_label: string;
  documents: AccessDecision[];
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";

export async function askAssistant(
  prompt: string,
  modelId: string,
  conversationId: string | null,
): Promise<AssistantAnswer> {
  const response = await fetch(`${apiBase}/api/v1/assistant/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({
      prompt,
      model_id: modelId,
      conversation_id: conversationId,
    }),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    const detail = typeof body?.detail === "string" ? body.detail : "";
    throw new Error(detail || `Assistant returned ${response.status}`);
  }
  return (await response.json()) as AssistantAnswer;
}
