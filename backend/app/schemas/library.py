"""Uploaded document list, chat, and admin sharing."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LibraryDocument(BaseModel):
    id: UUID
    filename: str
    space: str
    media_type: str
    extractor: str
    embedding_kind: str
    owner_id: UUID
    owner_name: str
    owner_email: str
    shared: bool
    excerpt: str
    created_at: datetime


class LibraryAskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    model_id: str | None = None
    conversation_id: UUID | None = None


class LibraryExcerpt(BaseModel):
    chunk_index: int
    content: str


class LibraryAskResponse(BaseModel):
    conversation_id: UUID
    document_id: UUID
    filename: str
    status: str
    answer: str | None
    error_message: str | None
    intent: str
    intent_label: str
    excerpts: list[LibraryExcerpt]


class ShareRequest(BaseModel):
    user_id: UUID


class DocumentAccess(BaseModel):
    user_id: UUID
    display_name: str
    email: str
    owner: bool
