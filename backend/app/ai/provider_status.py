"""Name the chat route and check whether each model option answers."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx

from app.ai.gateway import scrub
from app.core.config import Settings

Probe = Callable[[str, dict[str, str]], Awaitable[tuple[int, str]]]


@dataclass(frozen=True)
class ProviderCheck:
    id: str
    name: str
    state: str
    active: bool
    detail: str


def active_route(settings: Settings) -> tuple[str, str]:
    """Return the route id and the label shown in the UI."""
    base = settings.chat_api_base.strip().lower()
    model = settings.chat_model.strip()
    if ":4000" in base:
        return "litellm", "LiteLLM proxy"
    if model.startswith("ollama/") or ":11434" in base or "ollama" in base:
        return "ollama", "Local Ollama"
    if settings.chat_provider == "openai" and (not base or "api.openai.com" in base):
        return "openai", "OpenAI"
    return "other", "Other model endpoint"


def configured_model_name(settings: Settings) -> str:
    model = settings.chat_model.strip()
    if "/" in model:
        return model.split("/", 1)[1]
    return model


async def check_providers(settings: Settings, probe: Probe | None = None) -> list[ProviderCheck]:
    fetch = probe or _probe
    route_id, _label = active_route(settings)
    ollama = await _ollama(settings, fetch, active=route_id == "ollama")
    openai = await _openai(settings, fetch, active=route_id == "openai")
    proxy = await _proxy(settings, fetch, active=route_id == "litellm")
    return [openai, ollama, proxy]


async def _probe(url: str, headers: dict[str, str]) -> tuple[int, str]:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        return 0, scrub(str(exc)) or type(exc).__name__
    return response.status_code, scrub(response.text[:8000]) or ""


async def _ollama(settings: Settings, probe: Probe, *, active: bool) -> ProviderCheck:
    status, body = await probe("http://127.0.0.1:11434/api/tags", {})
    name = configured_model_name(settings)
    if status != 200:
        if status == 0:
            detail = "Ollama is not running on 127.0.0.1:11434"
        else:
            detail = f"Ollama returned HTTP {status}"
        return ProviderCheck("ollama", "Local Ollama", "down", active, detail)
    if active and name and name not in body:
        return ProviderCheck(
            "ollama",
            "Local Ollama",
            "down",
            active,
            f"Ollama is running, but {name} is not installed",
        )
    if "qwen2.5:3b" in body:
        installed = " with qwen2.5:3b"
    elif active and name:
        installed = f" with {name}"
    else:
        installed = ""
    return ProviderCheck("ollama", "Local Ollama", "up", active, f"Ollama is running{installed}")


async def _openai(settings: Settings, probe: Probe, *, active: bool) -> ProviderCheck:
    if not settings.openai_configured:
        return ProviderCheck("openai", "OpenAI", "down", active, "No OpenAI API key is set")
    status, body = await probe(
        "https://api.openai.com/v1/models",
        {"Authorization": f"Bearer {settings.openai_api_key}"},
    )
    if status == 200:
        return ProviderCheck(
            "openai",
            "OpenAI",
            "up",
            active,
            "The OpenAI key was accepted. A chat completion still spends credits.",
        )
    if status == 0:
        detail = body or "OpenAI could not be reached"
        return ProviderCheck("openai", "OpenAI", "down", active, detail)
    lowered = body.lower()
    if "credit" in lowered or status == 429:
        detail = "OpenAI rejected the key: no credits remaining"
        return ProviderCheck("openai", "OpenAI", "down", active, detail)
    return ProviderCheck("openai", "OpenAI", "down", active, f"OpenAI returned HTTP {status}")


async def _proxy(settings: Settings, probe: Probe, *, active: bool) -> ProviderCheck:
    status, _body = await probe("http://127.0.0.1:4000/health/liveliness", {})
    if status != 200:
        if status == 0:
            detail = "No LiteLLM proxy is listening on port 4000"
        else:
            detail = f"LiteLLM proxy returned HTTP {status}"
        return ProviderCheck("litellm", "LiteLLM proxy", "down", active, detail)
    if not active:
        detail = "LiteLLM proxy is listening on port 4000"
        return ProviderCheck("litellm", "LiteLLM proxy", "up", active, detail)
    alias = settings.chat_alias.strip() or "chat-default"
    if not settings.litellm_master_key.strip():
        detail = "Proxy is listening, but LITELLM_MASTER_KEY is not set"
        return ProviderCheck("litellm", "LiteLLM proxy", "down", active, detail)
    model_status, body = await probe(
        "http://127.0.0.1:4000/v1/models",
        {"Authorization": f"Bearer {settings.litellm_master_key}"},
    )
    if model_status == 200 and alias in body:
        detail = f"{alias} is registered on the LiteLLM proxy"
        return ProviderCheck("litellm", "LiteLLM proxy", "up", active, detail)
    if model_status == 200:
        detail = f"Proxy is listening, but {alias} is not registered"
        return ProviderCheck("litellm", "LiteLLM proxy", "down", active, detail)
    detail = f"LiteLLM proxy model list returned HTTP {model_status}"
    return ProviderCheck("litellm", "LiteLLM proxy", "down", active, detail)
