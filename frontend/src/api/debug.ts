export interface GatewayStatus {
  provider: string;
  model_alias: string;
  model: string;
  api_base: string;
  active_label: string;
  configured: boolean;
  timeout_seconds: number;
  max_retries: number;
  trace_dialect: string;
  trace_count: number;
}

export interface ProviderCheck {
  id: string;
  name: string;
  state: "up" | "down";
  active: boolean;
  detail: string;
}

export interface ProviderReport {
  active_label: string;
  model: string;
  api_base: string;
  providers: ProviderCheck[];
}

export interface LlmTrace {
  id: string;
  created_at: string;
  source: string;
  provider: string;
  model_alias: string;
  model: string;
  status: string;
  latency_ms: number | null;
  timeout_seconds: number;
  max_retries: number;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  request_messages: { role: string; content: string }[];
  response_text: string | null;
  provider_response_id: string | null;
  error_type: string | null;
  error_message: string | null;
}

export interface TraceList {
  items: LlmTrace[];
  total: number;
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";

async function readJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`);
  if (!response.ok) {
    throw new Error(`${path} returned ${response.status}`);
  }
  return (await response.json()) as T;
}

export function loadGatewayStatus(): Promise<GatewayStatus> {
  return readJson<GatewayStatus>("/api/v1/debug/openai");
}

export function loadProviderStatus(): Promise<ProviderReport> {
  return readJson<ProviderReport>("/api/v1/debug/providers");
}

export function loadTraces(status: string): Promise<TraceList> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return readJson<TraceList>(`/api/v1/debug/traces${query}`);
}

export async function sendDebugPrompt(prompt: string): Promise<LlmTrace> {
  const response = await fetch(`${apiBase}/api/v1/debug/traces/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!response.ok) {
    throw new Error(`Debug prompt returned ${response.status}`);
  }
  return (await response.json()) as LlmTrace;
}
