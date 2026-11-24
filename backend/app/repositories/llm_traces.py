"""Persistence for model-call traces."""

from pathlib import Path
from typing import cast

import structlog
from sqlalchemy import Table, func, select
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.models import Base
from app.models.llm_trace import LLMTrace

log = structlog.get_logger(__name__)

_engine: AsyncEngine | None = None


def trace_dialect() -> str:
    url = get_settings().trace_database_url
    return url.split("+", 1)[0].split(":", 1)[0]


def _ensure_sqlite_parent(url: str) -> None:
    if not url.startswith("sqlite"):
        return
    path = url.split("///", 1)[-1]
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_trace_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        url = get_settings().trace_database_url
        _ensure_sqlite_parent(url)
        _engine = create_async_engine(url)
    return _engine


def _sessions() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_trace_engine(), expire_on_commit=False)


async def init_trace_store() -> None:
    def create_trace_table(connection: Connection) -> None:
        Base.metadata.create_all(connection, tables=[cast(Table, LLMTrace.__table__)])

    async with get_trace_engine().begin() as connection:
        await connection.run_sync(create_trace_table)
    log.info("trace_store_ready", dialect=trace_dialect())


async def dispose_trace_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def save_trace(trace: LLMTrace) -> LLMTrace:
    async with _sessions()() as session:
        session.add(trace)
        await session.commit()
        await session.refresh(trace)
        return trace


async def get_trace(trace_id: str) -> LLMTrace | None:
    async with _sessions()() as session:
        return await session.get(LLMTrace, trace_id)


async def list_traces(
    *,
    status: str | None,
    limit: int,
    offset: int,
) -> tuple[list[LLMTrace], int]:
    filters = []
    if status:
        filters.append(LLMTrace.status == status)
    async with _sessions()() as session:
        total = await session.scalar(select(func.count()).select_from(LLMTrace).where(*filters))
        rows = await session.scalars(
            select(LLMTrace)
            .where(*filters)
            .order_by(LLMTrace.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows), int(total or 0)
