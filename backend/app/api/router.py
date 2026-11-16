"""Top-level API router."""

from fastapi import APIRouter

from app.api.debug import router as debug_router
from app.api.health import router as health_router
from app.api.worldbank import router as worldbank_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(debug_router)
api_router.include_router(worldbank_router)
