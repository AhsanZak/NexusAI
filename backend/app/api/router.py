"""Top-level API router."""

from fastapi import APIRouter

from app.api.access import router as access_router
from app.api.admin_users import router as admin_users_router
from app.api.assistant import router as assistant_router
from app.api.auth import router as auth_router
from app.api.authz import router as authz_router
from app.api.chat import router as chat_router
from app.api.debug import router as debug_router
from app.api.health import router as health_router
from app.api.knowledge import router as knowledge_router
from app.api.library import router as library_router
from app.api.olist import router as olist_router
from app.api.permissions import router as permissions_router
from app.api.worldbank import router as worldbank_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(admin_users_router)
api_router.include_router(permissions_router)
api_router.include_router(access_router)
api_router.include_router(authz_router)
api_router.include_router(assistant_router)
api_router.include_router(debug_router)
api_router.include_router(worldbank_router)
api_router.include_router(olist_router)
api_router.include_router(knowledge_router)
api_router.include_router(library_router)
