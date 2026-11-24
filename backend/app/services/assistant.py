"""Build a chat prompt from the documents OpenFGA allowed for one user."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.ai.gateway import LLMCallError, complete
from app.authz.client import PermissionChecker
from app.authz.demo import DOCUMENTS, USERS
from app.intent import UserIntent, apply_intent, classify_intent
from app.services.authorization import AccessDecision, collect_decisions
from app.services.chat_context import append_prior

Complete = Callable[..., Awaitable[object]]


class UnknownUserError(Exception):
    """The caller is not one of the users OpenFGA knows."""


@dataclass(frozen=True)
class AssistantAnswer:
    user_id: str
    display_name: str
    role: str
    status: str
    answer: str | None
    error_message: str | None
    decisions: list[AccessDecision]
    intent: UserIntent


def messages_for(
    decisions: list[AccessDecision],
    question: str,
    prior: list[dict[str, str]] | None = None,
    *,
    needs_documents: bool = True,
) -> list[dict[str, object]]:
    """Include allowed document text only when the question asks for documents."""
    if not needs_documents:
        system = (
            "Answer the user's question directly. "
            "Do not search the documents and do not say a document is missing or not allowed. "
            "Use earlier turns in this chat when the question refers to them."
        )
        return append_prior(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            prior or [],
        )
    lines = [
        f"{item.object_name}: {item.content}"
        for item in decisions
        if item.allowed and item.content
    ]
    listed = "\n".join(lines) if lines else "None."
    system = (
        "The question asks about the documents below. "
        "If it needs a document that is not listed, say you are not allowed to use it. "
        "Do not invent the missing text.\n\n"
        f"Documents:\n{listed}"
    )
    return append_prior(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
        prior or [],
    )


async def ask_subject(
    subject: str,
    display_name: str,
    role: str,
    question: str,
    checker: PermissionChecker,
    call_model: Complete = complete,
    *,
    prior: list[dict[str, str]] | None = None,
    intent: UserIntent | None = None,
) -> AssistantAnswer:
    """Ask as the OpenFGA subject for the signed-in account."""
    chosen = intent or classify_intent(question, prior)
    decisions: list[AccessDecision] = []
    if chosen.needs_documents:
        decisions = await _decisions(subject, display_name, role, checker)
    return await _finish(
        subject,
        display_name,
        role,
        question,
        decisions,
        call_model,
        prior,
        chosen,
    )


async def ask_user(
    user_id: str,
    question: str,
    checker: PermissionChecker,
    call_model: Complete = complete,
) -> AssistantAnswer:
    user = next((item for item in USERS if item.user_id == user_id), None)
    if user is None:
        raise UnknownUserError(user_id)
    chosen = classify_intent(question, None)
    decisions: list[AccessDecision] = []
    if chosen.needs_documents:
        decisions = [
            item for item in await collect_decisions(checker) if item.user_id == user.user_id
        ]
    return await _finish(
        user.user_id,
        user.display_name,
        user.role,
        question,
        decisions,
        call_model,
        None,
        chosen,
    )


async def _finish(
    user_id: str,
    display_name: str,
    role: str,
    question: str,
    decisions: list[AccessDecision],
    call_model: Complete,
    prior: list[dict[str, str]] | None,
    intent: UserIntent,
) -> AssistantAnswer:
    chosen = intent
    messages = apply_intent(
        messages_for(decisions, question, prior, needs_documents=chosen.needs_documents),
        chosen,
    )
    try:
        trace = await call_model(messages, source="assistant")
    except LLMCallError as exc:
        trace = exc.trace
    return AssistantAnswer(
        user_id=user_id,
        display_name=display_name,
        role=role,
        status=str(getattr(trace, "status", "error")),
        answer=getattr(trace, "response_text", None),
        error_message=getattr(trace, "error_message", None),
        decisions=decisions,
        intent=chosen,
    )


async def _decisions(
    subject: str,
    display_name: str,
    role: str,
    checker: PermissionChecker,
) -> list[AccessDecision]:
    decisions: list[AccessDecision] = []
    for document in DOCUMENTS:
        allowed = await checker.check(subject, document.relation, document.object_id)
        decisions.append(
            AccessDecision(
                user_id=subject,
                display_name=display_name,
                role=role,
                relation=document.relation,
                object_id=document.object_id,
                object_name=document.name,
                shared=False,
                allowed=allowed,
                content=document.content if allowed else None,
            )
        )
    return decisions
