"""Async database engine. Schema changes belong in Alembic, not here."""

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import get_settings

log = structlog.get_logger(__name__)


def create_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(settings.database_url, pool_pre_ping=True)


engine = create_engine()


async def check_database() -> bool:
    """Return whether PostgreSQL accepts a trivial query. Failures stay out of the response body."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        log.warning("database_check_failed", error_type=type(exc).__name__)
        return False
    return True
