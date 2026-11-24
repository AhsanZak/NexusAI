"""The chat models a person can choose. Names are the product names, nothing extra."""

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx

from app.ai.gateway import scrub
from app.core.config import Settings

Probe = Callable[[str, dict[str, str]], Awaitable[tuple[int, str]]]

LOCAL = "local-ollama"
SMART = "smart-ollama"
OPENAI = "openai"
LITELLM = "litellm"
DEFAULT_MODEL = SMART

NAMES = {
    LOCAL: "Local Ollama",
    SMART: "Smart Ollama",
    OPENAI: "OpenAI",
    LITELLM: "LiteLLM",
}

_EMBEDDING_MARKERS = ("bge", "embed", "nomic")


class UnknownModel(Exception):
    """The requested model is not one of the choices."""


@dataclass(frozen=True)
class ModelChoice:
    id: str
    name: str
    state: str
    detail: str
    chat_model: str
    chat_api_base: str


def active_choice_id(settings: Settings) -> str:
    """Which choice matches the process default, before a person picks one."""
    base = settings.chat_api_base.strip().lower()
    model = settings.chat_model.strip()
    if ":4000" in base:
        return LITELLM
    if "127.0.0.1:11434" in base or "localhost:11434" in base:
        return LOCAL
    if model.startswith("ollama/") or ":11434" in base:
        return SMART
    if settings.chat_provider == "openai" and (not base or "api.openai.com" in base):
        return OPENAI
    return "other"


def settings_for(settings: Settings, choice: ModelChoice) -> Settings:
    timeout = settings.llm_timeout_seconds
    if choice.id in {LOCAL, SMART}:
        timeout = max(timeout, 180)
    return settings.model_copy(
        update={
            "chat_model": choice.chat_model,
            "chat_api_base": choice.chat_api_base,
            "chat_alias": choice.name,
            "llm_timeout_seconds": timeout,
        }
    )


async def model_choices(settings: Settings, probe: Probe | None = None) -> list[ModelChoice]:
    fetch = probe or _probe
    smart_names = await _ollama_names(fetch, settings.ollama_base_url)
    return [
        _local(settings, smart_names),
        await _smart(settings, smart_names, fetch),
        await _openai(settings, fetch),
        await _litellm(settings, fetch),
    ]


def require_choice(choices: list[ModelChoice], model_id: str) -> ModelChoice:
    match = next((item for item in choices if item.id == model_id), None)
    if match is None:
        raise UnknownModel(model_id)
    return match


def _local(settings: Settings, names: list[str] | None) -> ModelChoice:
    """Local Ollama uses the Smart Ollama server, not the model on this machine."""
    host = settings.ollama_base_url.rstrip("/")
    model = settings.ollama_chat_model.strip() or "qwen3.8:27b"
    if names is None:
        return _down(LOCAL, "Smart Ollama is not running", f"ollama/{model}", host)
    if model not in names:
        return _down(LOCAL, f"{model} is not installed", f"ollama/{model}", host)
    return ModelChoice(LOCAL, NAMES[LOCAL], "up", model, f"ollama/{model}", host)


async def _smart(
    settings: Settings,
    names: list[str] | None,
    probe: Probe,
) -> ModelChoice:
    """Send Smart Ollama through LiteLLM so the proxy can record it and fall back."""
    model = settings.ollama_chat_model.strip() or "qwen3.8:27b"
    routed = "openai/smart-ollama"
    proxy = "http://127.0.0.1:4000"
    if names is None:
        return _down(SMART, "Smart Ollama is not running", routed, proxy)
    if model not in names:
        return _down(SMART, f"{model} is not installed", routed, proxy)
    status, _body = await probe(f"{proxy}/health/liveliness", {})
    if status != 200:
        detail = "LiteLLM is not running" if status == 0 else f"LiteLLM returned HTTP {status}"
        return _down(SMART, detail, routed, proxy)
    if not settings.litellm_master_key.strip():
        return _down(SMART, "No LiteLLM key is set", routed, proxy)
    listed, body = await probe(
        f"{proxy}/v1/models",
        {"Authorization": f"Bearer {settings.litellm_master_key}"},
    )
    if listed == 200 and "smart-ollama" in body:
        return ModelChoice(
            SMART,
            NAMES[SMART],
            "up",
            f"{model}, falls back to OpenAI",
            routed,
            proxy,
        )
    if listed == 200:
        return _down(SMART, "smart-ollama is not registered in LiteLLM", routed, proxy)
    return _down(SMART, f"LiteLLM returned HTTP {listed}", routed, proxy)


async def _openai(settings: Settings, probe: Probe) -> ModelChoice:
    model = f"openai/{settings.openai_model.strip() or 'gpt-4o-mini'}"
    if not settings.openai_configured:
        return _down(OPENAI, "No OpenAI API key is set", model, "")
    status, body = await probe(
        "https://api.openai.com/v1/models",
        {"Authorization": f"Bearer {settings.openai_api_key}"},
    )
    if status == 200:
        return ModelChoice(OPENAI, NAMES[OPENAI], "up", settings.openai_model, model, "")
    if status == 0:
        return _down(OPENAI, body or "OpenAI could not be reached", model, "")
    if "credit" in body.lower() or status == 429:
        return _down(OPENAI, "OpenAI rejected the key: no credits remaining", model, "")
    return _down(OPENAI, f"OpenAI returned HTTP {status}", model, "")


async def _litellm(settings: Settings, probe: Probe) -> ModelChoice:
    model = "openai/chat-default"
    base = "http://127.0.0.1:4000"
    status, _body = await probe(f"{base}/health/liveliness", {})
    if status != 200:
        detail = "LiteLLM is not running" if status == 0 else f"LiteLLM returned HTTP {status}"
        return _down(LITELLM, detail, model, base)
    if not settings.litellm_master_key.strip():
        return _down(LITELLM, "No LiteLLM key is set", model, base)
    listed, body = await probe(
        f"{base}/v1/models",
        {"Authorization": f"Bearer {settings.litellm_master_key}"},
    )
    if listed == 200 and "chat-default" in body:
        return ModelChoice(
            LITELLM,
            NAMES[LITELLM],
            "up",
            "chat-default, falls back to OpenAI",
            model,
            base,
        )
    if listed == 200:
        return _down(LITELLM, "chat-default is not registered", model, base)
    return _down(LITELLM, f"LiteLLM returned HTTP {listed}", model, base)


def _down(choice_id: str, detail: str, chat_model: str, api_base: str) -> ModelChoice:
    return ModelChoice(choice_id, NAMES[choice_id], "down", detail, chat_model, api_base)


def _chat_model_name(names: list[str]) -> str | None:
    chat = [
        name for name in names if not any(marker in name.lower() for marker in _EMBEDDING_MARKERS)
    ]
    qwen = [name for name in chat if "qwen" in name.lower()]
    if qwen:
        return qwen[0]
    return chat[0] if chat else None


async def _ollama_names(probe: Probe, base_url: str) -> list[str] | None:
    status, body = await probe(f"{base_url.rstrip('/')}/api/tags", {})
    if status != 200:
        return None
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return []
    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        return []
    names: list[str] = []
    for item in models:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            names.append(item["name"])
    return names


async def _probe(url: str, headers: dict[str, str]) -> tuple[int, str]:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        return 0, scrub(str(exc)) or type(exc).__name__
    return response.status_code, scrub(response.text[:8000]) or ""
