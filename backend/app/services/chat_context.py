"""Keep one chat's earlier turns in the next prompt for that same chat."""

from typing import cast

_PRIOR_MESSAGES = 16
_PRIOR_CHARS = 12000


def title_from(prompt: str) -> str:
    compact = " ".join(prompt.split())
    if len(compact) <= 60:
        return compact or "New chat"
    return compact[:57] + "..."


def append_prior(
    messages: list[dict[str, object]],
    prior: list[dict[str, str]],
) -> list[dict[str, object]]:
    """Place this chat's earlier turns between the instructions and the new question."""
    if not prior or len(messages) < 2:
        return messages
    kept = _trim(prior)
    if not kept:
        return messages
    earlier = cast(list[dict[str, object]], kept)
    return [messages[0], *earlier, messages[-1]]


def _trim(prior: list[dict[str, str]]) -> list[dict[str, str]]:
    recent = [
        turn
        for turn in prior[-_PRIOR_MESSAGES:]
        if turn.get("role") in {"user", "assistant"} and turn.get("content")
    ]
    while recent and sum(len(turn["content"]) for turn in recent) > _PRIOR_CHARS:
        recent = recent[1:]
    return recent
