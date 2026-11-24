"""Shared API test client."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_TRACE_DB = Path(__file__).resolve().parents[1] / "data" / "debug" / "pytest_traces.db"
_TRACE_DB.parent.mkdir(parents=True, exist_ok=True)
os.environ["NEXUS_TRACE_DATABASE_URL"] = f"sqlite+aiosqlite:///{_TRACE_DB}"
# A developer .env may contain a real key and a local model. Tests stay on the default alias.
os.environ["OPENAI_API_KEY"] = ""
os.environ["LITELLM_MASTER_KEY"] = ""
os.environ["NEXUS_CHAT_ALIAS"] = "chat-default"
os.environ["NEXUS_CHAT_MODEL"] = "openai/gpt-4o-mini"
os.environ["NEXUS_CHAT_API_BASE"] = ""


@pytest.fixture
def client() -> TestClient:
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    return TestClient(create_app())
