"""Shared API test client."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_TRACE_DB = Path(__file__).resolve().parents[1] / "data" / "debug" / "pytest_traces.db"
_TRACE_DB.parent.mkdir(parents=True, exist_ok=True)
os.environ["NEXUS_TRACE_DATABASE_URL"] = f"sqlite+aiosqlite:///{_TRACE_DB}"


@pytest.fixture
def client() -> TestClient:
    from app.main import create_app

    return TestClient(create_app())
