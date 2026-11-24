"""The knowledge spaces and chats shown on the dashboard."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class KnowledgeSpaceCard(BaseModel):
    id: str
    label: str
    summary: str
    placeholder: str
    extensions: list[str]
    document_count: int
    conversation_count: int


class KnowledgeConversation(BaseModel):
    id: UUID
    title: str
    space: str | None
    space_label: str
    document_id: UUID | None
    filename: str | None
    intent_label: str | None
    updated_at: datetime


class KnowledgeHome(BaseModel):
    spaces: list[KnowledgeSpaceCard]
    conversations: list[KnowledgeConversation]
