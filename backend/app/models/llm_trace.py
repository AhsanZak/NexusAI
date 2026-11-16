"""Stored record of one model call. The API key is never a column."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class LLMTrace(Base):
    __tablename__ = "llm_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
    source: Mapped[str] = mapped_column(String(64))
    provider: Mapped[str] = mapped_column(String(64))
    model_alias: Mapped[str] = mapped_column(String(128))
    model: Mapped[str] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(16), index=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    timeout_seconds: Mapped[float] = mapped_column(Float)
    max_retries: Mapped[int] = mapped_column(Integer)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_messages: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_response_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
