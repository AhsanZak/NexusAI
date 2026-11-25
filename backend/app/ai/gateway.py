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


def _scrub_secret(value: str, secret: str) -> str | None:
    cleaned = value
    token = secret.strip()
    if token:
        cleaned = cleaned.replace(token, "[redacted]")
    return scrub(cleaned)


def _is_litellm_proxy(api_base: str) -> bool:
    return ":4000" in api_base.lower()


def _gateway_api_key(settings: Settings, api_base: str) -> str:
    """Choose the credential for this route. The proxy key never goes to Ollama or OpenAI."""
    if _is_litellm_proxy(api_base):
        return settings.litellm_master_key
    if api_base:
        return "local-free"
    if settings.chat_provider == "openai":
        return settings.openai_api_key
    return ""


def scrub_messages(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for message in messages:
        cleaned.append(
            {
                "role": str(message.get("role", "user")),
                "content": _scrub_content(message.get("content", "")),
            }
        )
    return cleaned


def _scrub_content(content: Any) -> str:
    if isinstance(content, str):
        return scrub(content) or ""
    if not isinstance(content, list):
        return scrub(str(content)) or ""
    texts: list[str] = []
    images = 0
    for part in content:
        if not isinstance(part, dict):
            continue
        if part.get("type") == "text":
            texts.append(scrub(str(part.get("text", ""))) or "")
        elif part.get("type") == "image_url":
            images += 1
    text = "\n".join(item for item in texts if item)
    if images:
        note = f"[{images} image attached]"
        text = f"{text}\n{note}" if text else note
    return text


async def call_model(
    *,
    model: str,
    messages: list[dict[str, Any]],
    api_key: str,
    api_base: str,
    timeout: float,
    num_retries: int,
    temperature: float | None = None,
) -> Any:
    """The only function that imports LiteLLM."""
    import litellm
    from litellm import acompletion

    litellm.telemetry = False
    litellm.drop_params = True
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "timeout": timeout,
        "num_retries": num_retries,
    }
    if api_key:
        kwargs["api_key"] = api_key
    if api_base:
        kwargs["api_base"] = api_base
    if temperature is not None:
        kwargs["temperature"] = temperature
    kwargs.update(direct_ollama_kwargs(model, api_base))
    return await acompletion(**kwargs)


_PROXY_OLLAMA = {
    "openai/smart-ollama",
    "openai/chat-default",
    "openai/local-ollama",
}


def direct_ollama_kwargs(model: str, api_base: str) -> dict[str, str]:
    """Turn off Qwen thinking. The proxy drops this parameter on an OpenAI fallback."""
    through_proxy = _is_litellm_proxy(api_base) and model in _PROXY_OLLAMA
    if through_proxy or model.startswith("ollama/") or ":11434" in api_base:
        return {"reasoning_effort": "none"}
    return {}


def _usage_count(usage: Any, name: str) -> int | None:
    if usage is None:
        return None
    value = getattr(usage, name, None)
    if value is None and isinstance(usage, dict):
        value = usage.get(name)
    return int(value) if value is not None else None


async def complete(
    messages: list[dict[str, Any]],
    *,
    source: str,
    settings: Settings | None = None,
    temperature: float | None = None,
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

    local_base = active.chat_api_base.strip()
    hosted_openai = active.chat_provider == "openai" and not local_base
    if "api.openai.com" in local_base.lower():
        base.error_type = "billing_blocked"
        base.error_message = "Refusing api.openai.com because that endpoint spends credits"
        base.latency_ms = round((time.perf_counter() - started) * 1000, 2)
        saved = await save_trace(base)
        raise LLMCallError(saved)
    if hosted_openai and not active.openai_configured:
        base.error_type = "not_configured"
        base.error_message = "OPENAI_API_KEY is not set"
        base.latency_ms = round((time.perf_counter() - started) * 1000, 2)
        saved = await save_trace(base)
        raise LLMCallError(saved)

    proxy = _is_litellm_proxy(local_base)
    if proxy and not active.litellm_master_key.strip():
        base.error_type = "not_configured"
        base.error_message = "LITELLM_MASTER_KEY is not set"
        base.latency_ms = round((time.perf_counter() - started) * 1000, 2)
        saved = await save_trace(base)
        raise LLMCallError(saved)

    try:
        provider_key = _gateway_api_key(active, local_base)
        text_only = all(isinstance(message.get("content"), str) for message in messages)
        response = await call_model(
            model=active.chat_model,
            messages=stored_messages if text_only else messages,
            api_key=provider_key,
            api_base=local_base,
            timeout=active.llm_timeout_seconds,
            num_retries=active.llm_max_retries,
            temperature=temperature,
        )
    except Exception as exc:
        base.error_type = type(exc).__name__
        base.error_message = _scrub_secret(str(exc), active.litellm_master_key)
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
