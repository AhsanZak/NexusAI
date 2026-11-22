"""Provider labels and health checks do not call a live model."""

import pytest

from app.ai.provider_status import active_route, check_providers, configured_model_name
from app.core.config import Settings


def _settings(**overrides: str) -> Settings:
    values = {
        "chat_model": "openai/qwen2.5:3b",
        "chat_api_base": "http://127.0.0.1:11434/v1",
        "openai_api_key": "sk-test-value-not-real",
    }
    values.update(overrides)
    return Settings(**values)


def test_local_openai_compatible_base_is_named_ollama() -> None:
    route_id, label = active_route(_settings())
    assert route_id == "ollama"
    assert label == "Local Ollama"
    assert configured_model_name(_settings()) == "qwen2.5:3b"


def test_hosted_openai_is_named_openai() -> None:
    route_id, label = active_route(_settings(chat_model="openai/gpt-4o-mini", chat_api_base=""))
    assert route_id == "openai"
    assert label == "OpenAI"


@pytest.mark.asyncio
async def test_provider_checks_mark_only_the_active_route() -> None:
    async def probe(url: str, _headers: dict[str, str]) -> tuple[int, str]:
        if url.endswith("/api/tags"):
            return 200, '{"models":[{"name":"qwen2.5:3b"}]}'
        if "api.openai.com" in url:
            return 429, "You have no credits remaining"
        return 200, "I'm alive!"

    checks = await check_providers(_settings(), probe)
    by_id = {item.id: item for item in checks}

    assert by_id["ollama"].state == "up"
    assert by_id["ollama"].active is True
    assert by_id["openai"].state == "down"
    assert by_id["openai"].active is False
    assert "credits" in by_id["openai"].detail
    assert by_id["litellm"].state == "up"
    assert by_id["litellm"].active is False
    assert "sk-" not in by_id["openai"].detail


@pytest.mark.asyncio
async def test_proxy_route_requires_the_registered_alias() -> None:
    async def probe(url: str, headers: dict[str, str]) -> tuple[int, str]:
        if url.startswith("http://127.0.0.1:4000/v1/models"):
            assert headers["Authorization"] == "Bearer sk-test-proxy-key"
            return 200, '{"data":[{"id":"chat-default"}]}'
        if url.endswith("/api/tags"):
            return 200, '{"models":[{"name":"qwen2.5:3b"}]}'
        if "api.openai.com" in url:
            return 429, "You have no credits remaining"
        return 200, "I'm alive!"

    settings = _settings(
        chat_model="openai/chat-default",
        chat_api_base="http://127.0.0.1:4000",
        litellm_master_key="sk-test-proxy-key",
    )
    checks = await check_providers(settings, probe)
    by_id = {item.id: item for item in checks}

    assert by_id["litellm"].state == "up"
    assert by_id["litellm"].active is True
    assert "chat-default" in by_id["litellm"].detail
    assert by_id["ollama"].state == "up"
    assert by_id["ollama"].active is False
    assert "sk-" not in by_id["litellm"].detail
