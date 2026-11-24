"""The model prompt contains only the documents OpenFGA allowed."""

from dataclasses import dataclass

import pytest

from app.authz.demo import DOCUMENTS, TUPLES
from app.services.assistant import ask_user, messages_for
from app.services.chat_context import append_prior, title_from


class _Allowed:
    def __init__(self, allowed: set[tuple[str, str, str]]) -> None:
        self.allowed = allowed

    async def check(self, user: str, relation: str, object_id: str) -> bool:
        return (user, relation, object_id) in self.allowed


@dataclass
class _Trace:
    status: str = "success"
    response_text: str | None = "answered"
    error_message: str | None = None


@pytest.mark.asyncio
async def test_denied_document_text_is_not_sent_to_the_model() -> None:
    seen: list[dict[str, str]] = []

    async def call_model(messages: list[dict[str, str]], *, source: str) -> _Trace:
        assert source == "assistant"
        seen.extend(messages)
        return _Trace()

    finance = DOCUMENTS[2].content
    sales = DOCUMENTS[1].content
    amina = await ask_user(
        "user:amina",
        "What do the finance review notes say?",
        _Allowed(set(TUPLES)),
        call_model,
    )
    prompt = "\n".join(item["content"] for item in seen)
    assert finance not in prompt
    assert sales in prompt
    assert amina.decisions[2].content is None

    seen.clear()
    luis = await ask_user(
        "user:luis",
        "What do the finance review notes say?",
        _Allowed(set(TUPLES)),
        call_model,
    )
    prompt = "\n".join(item["content"] for item in seen)
    assert finance in prompt
    assert sales not in prompt
    assert luis.decisions[1].content is None


def test_a_chat_sends_only_its_own_earlier_turns() -> None:
    earlier = [
        {"role": "user", "content": "The site code for Cairo is ZX-44."},
        {"role": "assistant", "content": "Cairo is ZX-44."},
    ]
    sent = messages_for([], "What was the code?", earlier)
    text = [str(item["content"]) for item in sent]

    assert text[0].startswith("The question asks about the documents below")
    assert "not allowed to use it" in text[0]
    assert text[1] == "The site code for Cairo is ZX-44."
    assert text[2] == "Cairo is ZX-44."
    assert text[3] == "What was the code?"
    assert "QM-17" not in "\n".join(text)
    assert append_prior(sent, []) == sent
    assert title_from("  Cairo   warehouse  ") == "Cairo warehouse"
