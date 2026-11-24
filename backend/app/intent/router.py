"""Ask the small model on Smart Ollama what the latest message is trying to do."""

import httpx
import structlog

from app.core.config import Settings, get_settings
from app.intent.classify import UserIntent, classify_intent, intent_by_name, parse_router_result

log = structlog.get_logger(__name__)

_SYSTEM = (
    "Read the latest user message first and decide what it is asking. "
    "It may be in any language. Do this before considering any document. "
    "Return JSON with intent and needs_documents. "
    "needs_documents is true only when the answer has to come from the account's "
    "documents, tables, figures, or permissions. "
    "needs_documents is false when the question can be answered without those documents, "
    "including questions about this chat or the assistant. "
    "access: asks which documents or data this person is allowed to use. "
    "summary: asks for a summary of those documents. "
    "clarify: asks what the previous answer meant, such as explain that or what do you mean. "
    "follow_up: refers to an earlier turn, such as those, the first, or you named. "
    "lookup: asks for a fact that is in the documents. "
    "new_topic: a new question that does not ask for those documents. "
    "Do not use follow_up or clarify when there are no earlier turns. "
    "A question about being allowed is access and needs_documents true. "
    "A question that is not about the documents is needs_documents false. "
    'Example: "which ai are you?" is new_topic and needs_documents false. '
    'Example: "What documents am I allowed to use?" is access and needs_documents true. '
    'Example: "Which of those did you name first?" after an earlier answer is follow_up '
    "and needs_documents true."
)


async def resolve_intent(
    prompt: str,
    prior: list[dict[str, str]] | None,
    settings: Settings | None = None,
) -> UserIntent:
    """Use qwen3:8b when it answers, and the keyword reading when it does not."""
    active = settings or get_settings()
    keyword = classify_intent(prompt, prior)
    try:
        routed = await _route(prompt, prior, active)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        log.warning("intent_router_failed", error_type=type(exc).__name__)
        routed = None
    if routed is None:
        return keyword
    # Explicit English cues stay with the keyword reading when the router
    # picks a neighboring intent. Other languages still use the router.
    if keyword.name == "access" and routed.name != "access":
        return keyword
    if keyword.name == "summary" and routed.name != "summary":
        return keyword
    if keyword.name == "follow_up" and routed.name == "clarify":
        return keyword
    return routed


async def _route(
    prompt: str,
    prior: list[dict[str, str]] | None,
    settings: Settings,
) -> UserIntent | None:
    model = settings.ollama_intent_model.strip() or "qwen3:8b"
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    body = {
        "model": model,
        "stream": False,
        "think": False,
        "keep_alive": "30m",
        "format": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": [
                        "access",
                        "summary",
                        "clarify",
                        "follow_up",
                        "lookup",
                        "new_topic",
                    ],
                },
                "needs_documents": {"type": "boolean"},
            },
            "required": ["intent", "needs_documents"],
        },
        "options": {"temperature": 0, "num_predict": 64, "num_ctx": 2048},
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _user_text(prompt, prior)},
        ],
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=body)
        response.raise_for_status()
        payload = response.json()
    message = payload.get("message") if isinstance(payload, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        return None
    parsed = parse_router_result(content)
    if parsed is None:
        return None
    name, needs_documents = parsed
    if name in {"follow_up", "clarify"} and not prior:
        return None
    return intent_by_name(name, needs_documents=needs_documents)


def _user_text(prompt: str, prior: list[dict[str, str]] | None) -> str:
    lines: list[str] = []
    for turn in (prior or [])[-4:]:
        content = " ".join(turn.get("content", "").split())[:400]
        role = turn.get("role", "user")
        if content:
            lines.append(f"{role}: {content}")
    history = "\n".join(lines) or "None."
    question = " ".join(prompt.split())[:2000]
    return f"Earlier turns:\n{history}\n\nLatest message:\n{question}"
