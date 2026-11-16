"""Health endpoint tests. Readiness uses a stub so these tests do not require PostgreSQL."""

import pytest
from fastapi.testclient import TestClient

from app.api import health as health_module
from app.core.config import get_settings


def test_liveness(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "nexusai-api"}


def test_readiness_when_database_accepts_queries(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def database_up() -> bool:
        return True

    monkeypatch.setattr(health_module, "check_database", database_up)

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "up"}


def test_readiness_when_database_is_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def database_down() -> bool:
        return False

    monkeypatch.setattr(health_module, "check_database", database_down)

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "database unavailable"


def test_unknown_route_is_json(client: TestClient) -> None:
    response = client.get("/api/v1/missing")

    assert response.status_code == 404
    assert "detail" in response.json()


def test_cors_origins_parse_as_a_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXUS_CORS_ORIGINS", "http://localhost:5173, http://localhost:8080")
    get_settings.cache_clear()

    try:
        assert get_settings().cors_origin_list == [
            "http://localhost:5173",
            "http://localhost:8080",
        ]
    finally:
        get_settings.cache_clear()
