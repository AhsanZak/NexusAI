"""Read one question against the chat it belongs to and name the intent."""

import json
import re
from dataclasses import dataclass

_TOKEN = re.compile(r"[^a-z0-9]+")

_ACCESS = ("allowed", "permission", "can i use", "am i allowed", "which documents")
_SUMMARY = ("summarize", "summary", "tl dr", "overview", "in brief")
_CLARIFY = ("what do you mean", "explain that", "clarify", "why did you", "say that again")
_FOLLOW = (
    "those",
    "that one",
    "the first",
    "the second",
    "previous",
    "earlier",
    "you said",
    "you named",
    "you mentioned",
    "again",
    "last answer",
    "what was",
    "which of",
)
_LOOKUP = (
    "what does",
    "what do",
    "what is",
    "table",
    "tables",
    "figure",
    "revenue",
    "how many",
    "code",
    "document",
    "documents",
)


@dataclass(frozen=True)
class UserIntent:
    name: str
    label: str
    instruction: str
    needs_documents: bool


_INTENTS: dict[str, UserIntent] = {
    "access": UserIntent(
        "access",
        "Access",
        "The user wants to know which documents this account may use. Answer from that list.",
        True,
    ),
    "summary": UserIntent(
        "summary",
        "Summary",
        "The user wants a short summary of material this account may use.",
        True,
    ),
    "clarify": UserIntent(
        "clarify",
        "Clarification",
        "The user wants the previous answer in this chat explained.",
        True,
    ),
    "follow_up": UserIntent(
        "follow_up",
        "Follow-up",
        "The user is continuing this chat. Resolve words such as that, those, and the first "
        "from the earlier turns.",
        True,
    ),
    "lookup": UserIntent(
        "lookup",
        "Document lookup",
        "The user wants a fact from the documents. Copy the relevant text.",
        True,
    ),
    "new_topic": UserIntent(
        "new_topic",
        "New topic",
        "The user is asking a new question in this chat.",
        False,
    ),
}

_DIRECT = (
    "Answer the question directly. "
    "Do not search the documents and do not say a document is missing or not allowed."
)


def classify_intent(prompt: str, prior: list[dict[str, str]] | None) -> UserIntent:
    """Name the intent of this question. Earlier turns come from this chat only."""
    text = _TOKEN.sub(" ", prompt.lower()).strip()
    has_prior = bool(prior)
    if _has(text, _ACCESS):
        return _INTENTS["access"]
    if _has(text, _SUMMARY):
        return _INTENTS["summary"]
    if has_prior and _has(text, _CLARIFY):
        return _INTENTS["clarify"]
    if has_prior and _has(text, _FOLLOW):
        return _INTENTS["follow_up"]
    if _has(text, _LOOKUP):
        return _INTENTS["lookup"]
    return _INTENTS["new_topic"]


def intent_by_name(name: str | None, *, needs_documents: bool | None = None) -> UserIntent | None:
    if name is None:
        return None
    base = _INTENTS.get(name)
    if base is None:
        return None
    if needs_documents is None or needs_documents == base.needs_documents:
        return base
    return UserIntent(base.name, base.label, base.instruction, needs_documents)


def parse_router_result(payload: str) -> tuple[str, bool] | None:
    """Read the intent and whether the answer has to come from the documents."""
    match = re.search(r"\{.*\}", payload, re.DOTALL)
    if match is None:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    name = data.get("intent")
    if not isinstance(name, str) or name not in _INTENTS:
        return None
    needs = data.get("needs_documents")
    if not isinstance(needs, bool):
        needs = _INTENTS[name].needs_documents
    return name, needs


def parse_intent_name(payload: str) -> str | None:
    parsed = parse_router_result(payload)
    if parsed is None:
        return None
    return parsed[0]


def label_for(name: str | None) -> str | None:
    if name is None:
        return None
    intent = _INTENTS.get(name)
    return intent.label if intent is not None else None


def apply_intent(
    messages: list[dict[str, object]],
    intent: UserIntent,
) -> list[dict[str, object]]:
    """Add what the user is asking. Document rules stay out when they are not needed."""
    if not messages:
        return messages
    instruction = intent.instruction if intent.needs_documents else _DIRECT
    system = dict(messages[0])
    content = str(system.get("content") or "")
    system["content"] = f"{content}\n\nUser intent: {intent.label}. {instruction}"
    return [system, *messages[1:]]


def _has(text: str, phrases: tuple[str, ...]) -> bool:
    padded = f" {text} "
    return any(f" {phrase} " in padded for phrase in phrases)
