"""Single entry point for chat models. Callers use an alias, not a provider SDK."""

import re
import time
from typing import Any

import structlog

from app.core.config import Settings, get_settings
from app.models.llm_trace import LLMTrace
from app.repositories.llm_traces import save_trace

log = structlog.get_logger(__name__)

_SECRET = re.compile(r"sk-[A-Za-z0-9_\-]{6,}")


class LLMCallError(Exception):
    """A model call failed after a trace row was stored."""

    def __init__(self, trace: LLMTrace) -> None:
        self.trace = trace
        super().__init__(trace.error_message or "model call failed")


def scrub(value: str | None) -> str | None:
    if value is None:
        return None
    return _SECRET.sub("[redacted]", value)


def scrub_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for message in messages:
        cleaned.append(
            {
                "role": message.get("role", "user"),
                "content": scrub(message.get("content", "")) or "",
            }
        )
    return cleaned


async def call_model(
    *,
    model: str,
    messages: list[dict[str, str]],
    api_key: str,
    timeout: float,
    num_retries: int,
) -> Any:
    """The only function that imports LiteLLM."""
    import litellm
    from litellm import acompletion

    litellm.telemetry = False
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "timeout": timeout,
        "num_retries": num_retries,
    }
    if api_key:
        kwargs["api_key"] = api_key
    return await acompletion(**kwargs)


def _usage_count(usage: Any, name: str) -> int | None:
    if usage is None:
        return None
    value = getattr(usage, name, None)
    if value is None and isinstance(usage, dict):
        value = usage.get(name)
    return int(value) if value is not None else None


async def complete(
    messages: list[dict[str, str]],
    *,
    source: str,
    settings: Settings | None = None,
) -> LLMTrace:
    """Call the configured alias and store the request, response, usage, and error."""
    active = settings or get_settings()
    started = time.perf_counter()
    stored_messages = scrub_messages(messages)
    base = LLMTrace(
        source=source,
        provider=active.chat_provider,
        model_alias=active.chat_alias,
        model=active.chat_model,
        status="error",
        timeout_seconds=active.llm_timeout_seconds,
        max_retries=active.llm_max_retries,
        request_messages=stored_messages,
    )

    if active.chat_provider == "openai" and not active.openai_configured:
        base.error_type = "not_configured"
        base.error_message = "OPENAI_API_KEY is not set"
        base.latency_ms = round((time.perf_counter() - started) * 1000, 2)
        saved = await save_trace(base)
        raise LLMCallError(saved)

    try:
        response = await call_model(
            model=active.chat_model,
            messages=stored_messages,
            api_key=active.openai_api_key,
            timeout=active.llm_timeout_seconds,
            num_retries=active.llm_max_retries,
        )
    except Exception as exc:
        base.error_type = type(exc).__name__
        base.error_message = scrub(str(exc))
        base.latency_ms = round((time.perf_counter() - started) * 1000, 2)
        log.warning("llm_call_failed", error_type=base.error_type, source=source)
        saved = await save_trace(base)
        raise LLMCallError(saved) from exc

    choice = response.choices[0]
    message = choice.message
    content = getattr(message, "content", None)
    usage = getattr(response, "usage", None)
    base.status = "success"
    base.response_text = content if isinstance(content, str) else None
    base.provider_response_id = getattr(response, "id", None)
    base.prompt_tokens = _usage_count(usage, "prompt_tokens")
    base.completion_tokens = _usage_count(usage, "completion_tokens")
    base.total_tokens = _usage_count(usage, "total_tokens")
    base.latency_ms = round((time.perf_counter() - started) * 1000, 2)
    log.info(
        "llm_call_completed",
        source=source,
        model=active.chat_alias,
        latency_ms=base.latency_ms,
        total_tokens=base.total_tokens,
    )
    return await save_trace(base)
