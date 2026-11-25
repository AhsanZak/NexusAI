"""Member checks follow the signed-in subject. Guest tuples do not leak into that prompt."""

import uuid

import pytest

from app.authz.demo import (
    AUTHORIZATION_MODEL,
    DOCUMENTS,
    GUEST_SUBJECT,
    InvalidGrant,
    member_subject,
    validate_grant,
)
from app.services.assistant import ask_subject


class _Allowed:
    def __init__(self, allowed: set[tuple[str, str, str]]) -> None:
        self.allowed = allowed

    async def check(self, user: str, relation: str, object_id: str) -> bool:
        return (user, relation, object_id) in self.allowed


class _Trace:
    status = "success"
    response_text = "answered"
    error_message = None


def test_member_subject_is_the_account_id() -> None:
    user_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    assert member_subject(user_id) == "user:11111111-1111-1111-1111-111111111111"
    assert member_subject(user_id) != GUEST_SUBJECT


def test_catalog_accepts_document_relations_and_feature_use() -> None:
    validate_grant("document:olist-sales", "analyst")
    validate_grant("feature:ai-model", "can_use")
    validate_grant("feature:analysis", "can_use")
    with pytest.raises(InvalidGrant):
        validate_grant("document:world-bank", "can_use")
    with pytest.raises(InvalidGrant):
        validate_grant("feature:analysis", "viewer")
    with pytest.raises(InvalidGrant):
        validate_grant("document:missing", "viewer")
    validate_grant("document:upload-11111111-1111-1111-1111-111111111111", "auditor")
    with pytest.raises(InvalidGrant):
        validate_grant("document:upload-11111111-1111-1111-1111-111111111111", "can_use")


def test_authorization_model_includes_features() -> None:
    types = {item["type"] for item in AUTHORIZATION_MODEL["type_definitions"]}
    assert "feature" in types


@pytest.mark.asyncio
async def test_guest_permission_is_not_sent_to_a_member() -> None:
    subject = "user:11111111-1111-1111-1111-111111111111"
    seen: list[dict[str, str]] = []

    async def call_model(messages: list[dict[str, str]], *, source: str) -> _Trace:
        assert source == "assistant"
        seen.extend(messages)
        return _Trace()

    finance = DOCUMENTS[2].content
    sales = DOCUMENTS[1].content
    result = await ask_subject(
        subject,
        "Luis Ortega",
        "member",
        "What do the finance review notes say?",
        _Allowed(
            {
                (subject, "auditor", "document:finance-reviews"),
                (subject, "viewer", "document:world-bank"),
                (GUEST_SUBJECT, "analyst", "document:olist-sales"),
            }
        ),
        call_model,
    )
    prompt = "\n".join(item["content"] for item in seen)
    assert finance in prompt
    assert sales not in prompt
    assert result.user_id == subject
    sales_decision = next(
        item for item in result.decisions if item.object_id == "document:olist-sales"
    )
    assert sales_decision.allowed is False
    assert sales_decision.content is None
