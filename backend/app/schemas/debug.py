"""Debug API payloads. These schemas never include an API key."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.llm_trace import LLMTrace


class ProviderStatus(BaseModel):
    id: str
    name: str
    state: str
    active: bool
    detail: str


class GatewayStatusResponse(BaseModel):
    provider: str
    model_alias: str
    model: str
    api_base: str
    active_label: str
    configured: bool
    timeout_seconds: float
    max_retries: int
    trace_dialect: str
    trace_count: int


class ProviderStatusResponse(BaseModel):
    active_label: str
    model: str
    api_base: str
    providers: list[ProviderStatus]


class TraceResponse(BaseModel):
    id: str
    created_at: datetime
    source: str
    provider: str
    model_alias: str
    model: str
    status: str
    latency_ms: float | None
    timeout_seconds: float
    max_retries: int
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    request_messages: list[dict[str, str]]
    response_text: str | None
    provider_response_id: str | None
    error_type: str | None
    error_message: str | None

    @classmethod
    def from_trace(cls, trace: LLMTrace) -> "TraceResponse":
        return cls(
            id=trace.id,
            created_at=trace.created_at,
            source=trace.source,
            provider=trace.provider,
            model_alias=trace.model_alias,
            model=trace.model,
            status=trace.status,
            latency_ms=trace.latency_ms,
            timeout_seconds=trace.timeout_seconds,
            max_retries=trace.max_retries,
            prompt_tokens=trace.prompt_tokens,
            completion_tokens=trace.completion_tokens,
            total_tokens=trace.total_tokens,
            request_messages=trace.request_messages,
            response_text=trace.response_text,
            provider_response_id=trace.provider_response_id,
            error_type=trace.error_type,
            error_message=trace.error_message,
        )


class TraceListResponse(BaseModel):
    items: list[TraceResponse]
    total: int


class DebugPromptRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
