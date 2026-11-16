"""FastAPI application factory."""

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app import __version__
from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.logging import configure_logging
from app.repositories.llm_traces import dispose_trace_engine, init_trace_store

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await init_trace_store()
    yield
    await engine.dispose()
    await dispose_trace_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        summary="Enterprise knowledge, analytics, and AI automation API",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def log_requests(request: Request, call_next: RequestResponseEndpoint) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        log.info(
            "request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return response

    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
