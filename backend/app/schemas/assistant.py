"""Chat request that names the user OpenFGA will check."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.authz import AccessDecisionResponse


class AssistantUserResponse(BaseModel):
    user_id: str
    display_name: str
    role: str


class AssistantAskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    model_id: str | None = None
    conversation_id: UUID | None = None


class AssistantAskResponse(BaseModel):
    conversation_id: UUID
    user_id: str
    display_name: str
    role: str
    status: str
    answer: str | None
    error_message: str | None
    intent: str
    intent_label: str
    documents: list[AccessDecisionResponse]
