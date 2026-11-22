"""OpenAI gateway and debug-trace tests. The provider call is replaced with a fake."""

import pytest
from fastapi.testclient import TestClient

from app.ai.gateway import LLMCallError, complete, scrub
from app.core.config import get_settings
from app.repositories.llm_traces import init_trace_store


class _Usage:
    prompt_tokens = 4
    completion_tokens = 6
    total_tokens = 10


class _Message:
    content = "pong"


class _Choice:
    message = _Message()


class _Response:
    id = "chatcmpl-test"
    choices = [_Choice()]
    usage = _Usage()


@pytest.fixture
def openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-value-not-real")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def trace_store() -> None:
    get_settings.cache_clear()
    await init_trace_store()


def test_openai_key_uses_the_standard_environment_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.openai_configured is True
        assert settings.chat_provider == "openai"
        assert "sk-from-env" not in repr(settings)
    finally:
        get_settings.cache_clear()


def test_secret_text_is_scrubbed() -> None:
    assert scrub("token sk-abc123456789") == "token [redacted]"


@pytest.mark.asyncio
async def test_missing_key_is_stored_as_an_error_trace(
    trace_store: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()

    with pytest.raises(LLMCallError) as caught:
        await complete([{"role": "user", "content": "hello"}], source="unit")

    assert caught.value.trace.status == "error"
    assert caught.value.trace.error_type == "not_configured"
    assert caught.value.trace.request_messages == [{"role": "user", "content": "hello"}]


@pytest.mark.asyncio
async def test_successful_call_stores_usage_and_hides_the_key(
    trace_store: None, openai_key: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, object] = {}

    async def fake_call(**kwargs: object) -> _Response:
        seen.update(kwargs)
        return _Response()

    monkeypatch.setattr("app.ai.gateway.call_model", fake_call)
    trace = await complete(
        [{"role": "user", "content": "ping sk-abc123456789"}],
        source="unit",
    )

    assert seen["api_key"] == "sk-test-value-not-real"
    assert seen["api_base"] == ""
    assert seen["model"] == "openai/gpt-4o-mini"
    assert seen["num_retries"] == 2
    assert trace.status == "success"
    assert trace.response_text == "pong"
    assert trace.provider_response_id == "chatcmpl-test"
    assert trace.total_tokens == 10
    assert trace.request_messages[0]["content"] == "ping [redacted]"


@pytest.mark.asyncio
async def test_local_openai_compatible_model_does_not_receive_the_openai_key(
    trace_store: None, openai_key: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NEXUS_CHAT_MODEL", "openai/qwen2.5:3b")
    monkeypatch.setenv("NEXUS_CHAT_API_BASE", "http://127.0.0.1:11434/v1")
    get_settings.cache_clear()
    seen: dict[str, object] = {}

    async def fake_call(**kwargs: object) -> _Response:
        seen.update(kwargs)
        return _Response()

    monkeypatch.setattr("app.ai.gateway.call_model", fake_call)
    trace = await complete([{"role": "user", "content": "ping"}], source="unit")

    assert seen["api_base"] == "http://127.0.0.1:11434/v1"
    assert seen["api_key"] == "local-free"
    assert "sk-" not in str(seen["api_key"])
    assert trace.status == "success"
    assert trace.response_text == "pong"


@pytest.mark.asyncio
async def test_proxy_route_sends_the_master_key_only(
    trace_store: None, openai_key: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NEXUS_CHAT_MODEL", "openai/chat-default")
    monkeypatch.setenv("NEXUS_CHAT_API_BASE", "http://127.0.0.1:4000")
    monkeypatch.setenv("LITELLM_MASTER_KEY", "sk-test-proxy-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-value-not-real")
    get_settings.cache_clear()
    seen: dict[str, object] = {}

    async def fake_call(**kwargs: object) -> _Response:
        seen.update(kwargs)
        return _Response()

    monkeypatch.setattr("app.ai.gateway.call_model", fake_call)
    trace = await complete([{"role": "user", "content": "ping"}], source="unit")

    assert seen["model"] == "openai/chat-default"
    assert seen["api_base"] == "http://127.0.0.1:4000"
    assert seen["api_key"] == "sk-test-proxy-key"
    assert trace.status == "success"


@pytest.mark.asyncio
async def test_provider_failure_is_stored(
    trace_store: None, openai_key: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_call(**_kwargs: object) -> _Response:
        raise TimeoutError("timed out")

    monkeypatch.setattr("app.ai.gateway.call_model", fake_call)

    with pytest.raises(LLMCallError) as caught:
        await complete([{"role": "user", "content": "ping"}], source="unit")

    assert caught.value.trace.status == "error"
    assert caught.value.trace.error_type == "TimeoutError"
    assert caught.value.trace.error_message == "timed out"


def test_debug_page_can_list_and_inspect_a_failed_call(client: TestClient) -> None:
    missing = client.post("/api/v1/debug/traces/test", json={"prompt": "hello from the debug page"})
    assert missing.status_code == 200
    body = missing.json()
    assert body["status"] == "error"
    assert body["error_type"] == "not_configured"
    assert "api_key" not in body
    assert "sk-" not in missing.text

    listing = client.get("/api/v1/debug/traces")
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1
    trace_id = body["id"]
    detail = client.get(f"/api/v1/debug/traces/{trace_id}")
    assert detail.status_code == 200
    assert detail.json()["request_messages"][0]["content"] == "hello from the debug page"

    status_response = client.get("/api/v1/debug/openai")
    assert status_response.status_code == 200
    payload = status_response.json()
    assert payload["configured"] is False
    assert payload["model_alias"] == "chat-default"
    assert "api_key" not in payload


def test_unknown_trace_is_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/debug/traces/missing")
    assert response.status_code == 404
