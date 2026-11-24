"""Let each signed-in person choose a model and read their own chat."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.choices import (
    DEFAULT_MODEL,
    ModelChoice,
    UnknownModel,
    model_choices,
    require_choice,
    settings_for,
)
from app.api.auth import current_user
from app.core.config import Settings, get_settings
from app.intent import label_for
from app.models.user import User
from app.repositories.chat import (
    conversation_for,
    conversations_for,
    create_conversation,
    delete_conversation,
    messages_for,
    save_selected_model,
    selected_model,
)
from app.repositories.uploads import get_document
from app.schemas.chat import (
    ChatTurn,
    ConversationSummary,
    ModelListResponse,
    ModelOption,
    ModelUpdateRequest,
)
from app.services.chat_context import title_from
from app.services.library import DocumentAccessError, DocumentNotFound, ensure_can_view

router = APIRouter(prefix="/chat", tags=["chat"])


class ConversationNotFound(Exception):
    """This account does not have that chat."""


async def open_conversation(
    user: User,
    conversation_id: uuid.UUID | None,
    document_id: uuid.UUID | None,
    prompt: str,
) -> tuple[uuid.UUID, list[dict[str, str]]]:
    """Return this chat and the earlier turns that belong only to it."""
    if document_id is not None:
        await ensure_can_view(user, document_id)
    if conversation_id is None:
        space = None
        if document_id is not None:
            document = await get_document(document_id)
            space = document.space if document is not None else None
        created = await create_conversation(user.id, document_id, title_from(prompt), space)
        return created, []
    row = await conversation_for(user.id, conversation_id)
    if row is None or row.document_id != document_id:
        raise ConversationNotFound
    stored = await messages_for(conversation_id)
    prior = [{"role": item.role, "content": item.content} for item in stored]
    return conversation_id, prior


def _options(choices: list[ModelChoice]) -> list[ModelOption]:
    options: list[ModelOption] = []
    for item in choices:
        options.append(
            ModelOption(id=item.id, name=item.name, state=item.state, detail=item.detail)
        )
    return options


@router.get("/models", response_model=ModelListResponse)
async def list_models(user: Annotated[User, Depends(current_user)]) -> ModelListResponse:
    choices = await model_choices(get_settings())
    selected = await selected_model(user.id)
    if selected not in {item.id for item in choices}:
        selected = DEFAULT_MODEL
    return ModelListResponse(selected=selected, models=_options(choices))


@router.put("/model", response_model=ModelListResponse)
async def update_model(
    body: ModelUpdateRequest,
    user: Annotated[User, Depends(current_user)],
) -> ModelListResponse:
    choices = await model_choices(get_settings())
    try:
        require_choice(choices, body.model_id)
    except UnknownModel as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Choose Local Ollama, Smart Ollama, OpenAI, or LiteLLM.",
        ) from exc
    await save_selected_model(user.id, body.model_id)
    return ModelListResponse(selected=body.model_id, models=_options(choices))


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    user: Annotated[User, Depends(current_user)],
    document_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[ConversationSummary]:
    if document_id is not None:
        await _view_document(user, document_id)
    rows = await conversations_for(user.id, document_id)
    return [
        ConversationSummary(
            id=row.id,
            title=row.title,
            document_id=row.document_id,
            intent=row.intent,
            intent_label=label_for(row.intent),
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_conversation(
    conversation_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
) -> None:
    removed = await delete_conversation(user.id, conversation_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That chat was not found")


@router.get("/history", response_model=list[ChatTurn])
async def chat_history(
    user: Annotated[User, Depends(current_user)],
    conversation_id: Annotated[uuid.UUID, Query()],
) -> list[ChatTurn]:
    row = await conversation_for(user.id, conversation_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That chat was not found")
    if row.document_id is not None:
        await _view_document(user, row.document_id)
    rows = await messages_for(conversation_id)
    return [
        ChatTurn(
            id=row.id,
            role=row.role,
            content=row.content,
            model_name=row.model_name,
            intent=row.intent,
            intent_label=label_for(row.intent),
            created_at=row.created_at,
        )
        for row in rows
    ]


async def _view_document(user: User, document_id: uuid.UUID) -> None:
    try:
        await ensure_can_view(user, document_id)
    except DocumentNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That document was not found",
        ) from exc
    except DocumentAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An admin has not granted this account access to that document",
        ) from exc


async def choice_settings(user: User, model_id: str | None) -> tuple[str, Settings]:
    """Return the display name and the settings for this person's model."""
    choices = await model_choices(get_settings())
    selected = model_id or await selected_model(user.id)
    try:
        choice = require_choice(choices, selected)
    except UnknownModel as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Choose Local Ollama, Smart Ollama, OpenAI, or LiteLLM.",
        ) from exc
    await save_selected_model(user.id, choice.id)
    return choice.name, settings_for(get_settings(), choice)
