"""OpenAI call inspection. This router records traffic; it does not decide permissions."""

from fastapi import APIRouter, HTTPException, Query, status

from app.ai.gateway import LLMCallError, complete
from app.core.config import get_settings
from app.repositories.llm_traces import get_trace, list_traces, trace_dialect
from app.schemas.debug import (
    DebugPromptRequest,
    GatewayStatusResponse,
    TraceListResponse,
    TraceResponse,
)

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/openai", response_model=GatewayStatusResponse)
async def openai_status() -> GatewayStatusResponse:
    settings = get_settings()
    _rows, total = await list_traces(status=None, limit=1, offset=0)
    return GatewayStatusResponse(
        provider=settings.chat_provider,
        model_alias=settings.chat_alias,
        model=settings.chat_model,
        configured=settings.openai_configured,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        trace_dialect=trace_dialect(),
        trace_count=total,
    )


@router.get("/traces", response_model=TraceListResponse)
async def traces(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> TraceListResponse:
    if status_filter not in (None, "success", "error"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid status",
        )
    rows, total = await list_traces(status=status_filter, limit=limit, offset=offset)
    return TraceListResponse(items=[TraceResponse.from_trace(row) for row in rows], total=total)


@router.get("/traces/{trace_id}", response_model=TraceResponse)
async def trace_detail(trace_id: str) -> TraceResponse:
    row = await get_trace(trace_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="trace not found")
    return TraceResponse.from_trace(row)


@router.post("/traces/test", response_model=TraceResponse)
async def send_test_prompt(body: DebugPromptRequest) -> TraceResponse:
    """Send one prompt through the gateway so the resulting trace can be inspected."""
    try:
        trace = await complete(
            [{"role": "user", "content": body.prompt}],
            source="debug-page",
        )
    except LLMCallError as exc:
        trace = exc.trace
    return TraceResponse.from_trace(trace)
