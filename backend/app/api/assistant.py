"""Chat for the signed-in account. OpenFGA runs before any document text reaches the model."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.gateway import complete
from app.api.auth import current_user
from app.api.chat import ConversationNotFound, choice_settings, open_conversation
from app.authz.client import OpenFGAError, get_openfga_client
from app.authz.demo import USERS, member_subject
from app.intent import resolve_intent
from app.models.user import User
from app.repositories.chat import add_exchange
from app.schemas.assistant import AssistantAskRequest, AssistantAskResponse, AssistantUserResponse
from app.schemas.authz import AccessDecisionResponse
from app.services.access import member_can_use
from app.services.assistant import ask_subject

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/users", response_model=list[AssistantUserResponse])
async def assistant_users() -> list[AssistantUserResponse]:
    return [
        AssistantUserResponse(user_id=user.user_id, display_name=user.display_name, role=user.role)
        for user in USERS
    ]


@router.post("/ask", response_model=AssistantAskResponse)
async def assistant_ask(
    body: AssistantAskRequest,
    user: Annotated[User, Depends(current_user)],
) -> AssistantAskResponse:
    client = get_openfga_client()
    try:
        allowed = await member_can_use(user, client, "feature:ai-model")
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You are signed in as a member. "
                    "The AI model permission is not granted for this account."
                ),
            )
        model_name, chat_settings = await choice_settings(user, body.model_id)
        conversation_id, prior = await open_conversation(
            user,
            body.conversation_id,
            None,
            body.prompt,
        )
        intent = await resolve_intent(body.prompt, prior)

        async def call_model(messages: list[dict[str, str]], *, source: str) -> object:
            return await complete(messages, source=source, settings=chat_settings)

        result = await ask_subject(
            member_subject(user.id),
            user.display_name,
            user.role,
            body.prompt,
            client,
            call_model,
            prior=prior,
            intent=intent,
        )
    except ConversationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That chat was not found",
        ) from exc
    except OpenFGAError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    answer = result.answer if result.status == "success" and result.answer else result.error_message
    await add_exchange(
        user.id,
        None,
        conversation_id,
        model_name,
        body.prompt,
        answer or "The model call failed.",
        result.intent.name,
    )
    return AssistantAskResponse(
        conversation_id=conversation_id,
        intent=result.intent.name,
        intent_label=result.intent.label,
        user_id=result.user_id,
        display_name=result.display_name,
        role=result.role,
        status=result.status,
        answer=result.answer,
        error_message=result.error_message,
        documents=[
            AccessDecisionResponse(
                user_id=item.user_id,
                display_name=item.display_name,
                role=item.role,
                relation=item.relation,
                object_id=item.object_id,
                object_name=item.object_name,
                shared=item.shared,
                allowed=item.allowed,
                content=item.content,
            )
            for item in result.decisions
        ],
    )
