"""Model choices and one person's chat history."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ModelOption(BaseModel):
    id: str
    name: str
    state: str
    detail: str


class ModelListResponse(BaseModel):
    selected: str
    models: list[ModelOption]


class ModelUpdateRequest(BaseModel):
    model_id: str = Field(min_length=1, max_length=40)


class ChatTurn(BaseModel):
    id: UUID
    role: str
    content: str
    model_name: str
    intent: str | None
    intent_label: str | None
    created_at: datetime


class ConversationSummary(BaseModel):
    id: UUID
    title: str
    document_id: UUID | None
    intent: str | None
    intent_label: str | None
    updated_at: datetime
