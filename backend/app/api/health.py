"""Liveness and readiness endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.database import check_database

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str


class ReadinessResponse(BaseModel):
    status: str
    database: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Process liveness. This does not check PostgreSQL."""
    return HealthResponse(status="ok", service="nexusai-api")


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness() -> ReadinessResponse:
    """Readiness. Returns 503 when the API cannot reach PostgreSQL."""
    if not await check_database():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        )
    return ReadinessResponse(status="ready", database="up")
