"""Document catalog and the OpenFGA model.

The Amina and Luis tuples remain the scripted example. Live member checks use
PostgreSQL grants written as OpenFGA tuples for user:<account id> or user:guest.
"""

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DemoUser:
    user_id: str
    display_name: str
    role: str


@dataclass(frozen=True)
class DemoDocument:
    object_id: str
    name: str
    relation: str
    content: str


USERS: tuple[DemoUser, ...] = (
    DemoUser("user:amina", "Amina Rahman", "Sales analyst"),
    DemoUser("user:luis", "Luis Ortega", "Finance reviewer"),
)

DOCUMENTS: tuple[DemoDocument, ...] = (
    DemoDocument(
        "document:world-bank",
        "World Bank indicators",
        "viewer",
        "Public indicator history for the twelve countries in the warehouse.",
    ),
    DemoDocument(
        "document:olist-sales",
        "Olist sales warehouse",
        "analyst",
        "Order, revenue, and delivery figures from the 2016–2018 snapshot.",
    ),
    DemoDocument(
        "document:finance-reviews",
        "Finance review notes",
        "auditor",
        "Review comments and payment exceptions held for finance.",
    ),
)

@dataclass(frozen=True)
class DemoFeature:
    object_id: str
    name: str
    relation: str
    summary: str


GUEST_SUBJECT = "user:guest"
DOCUMENT_RELATIONS: tuple[str, ...] = ("viewer", "analyst", "auditor")

FEATURES: tuple[DemoFeature, ...] = (
    DemoFeature(
        "feature:ai-model",
        "AI model",
        "can_use",
        "Send a question to the model. Document text is added only after a document allow.",
    ),
    DemoFeature(
        "feature:analysis",
        "Analysis",
        "can_use",
        "Open the analysis page for the Olist warehouse.",
    ),
)


class InvalidGrant(Exception):
    """The object and relation are not in the catalog."""


def member_subject(user_id: uuid.UUID) -> str:
    """OpenFGA user id for a PostgreSQL account. This is not the guest subject."""
    return f"user:{user_id}"


def validate_grant(object_id: str, relation: str) -> None:
    """Accept a catalog document relation, or can_use on the AI model and analysis."""
    if any(item.object_id == object_id for item in DOCUMENTS):
        if relation not in DOCUMENT_RELATIONS:
            raise InvalidGrant("A document relation is viewer, analyst, or auditor")
        return
    if any(item.object_id == object_id for item in FEATURES):
        if relation != "can_use":
            raise InvalidGrant("AI model and analysis use the can_use relation")
        return
    if object_id.startswith("document:upload-"):
        if relation not in DOCUMENT_RELATIONS:
            raise InvalidGrant("An uploaded document uses viewer, analyst, or auditor")
        return
    raise InvalidGrant("Unknown document or feature")


def object_name(object_id: str) -> str:
    for document in DOCUMENTS:
        if document.object_id == object_id:
            return document.name
    for feature in FEATURES:
        if feature.object_id == object_id:
            return feature.name
    return object_id


def object_type(object_id: str) -> str:
    if object_id.startswith("feature:"):
        return "feature"
    return "document"


# Direct tuples. OpenFGA is the only place that decides the checks below.
TUPLES: tuple[tuple[str, str, str], ...] = (
    ("user:amina", "viewer", "document:world-bank"),
    ("user:luis", "viewer", "document:world-bank"),
    ("user:amina", "analyst", "document:olist-sales"),
    ("user:luis", "auditor", "document:finance-reviews"),
)

AUTHORIZATION_MODEL: dict[str, Any] = {
    "schema_version": "1.1",
    "type_definitions": [
        {"type": "user"},
        {
            "type": "document",
            "relations": {
                "viewer": {"this": {}},
                "analyst": {"this": {}},
                "auditor": {"this": {}},
            },
            "metadata": {
                "relations": {
                    "viewer": {"directly_related_user_types": [{"type": "user"}]},
                    "analyst": {"directly_related_user_types": [{"type": "user"}]},
                    "auditor": {"directly_related_user_types": [{"type": "user"}]},
                }
            },
        },
        {
            "type": "feature",
            "relations": {"can_use": {"this": {}}},
            "metadata": {
                "relations": {
                    "can_use": {"directly_related_user_types": [{"type": "user"}]},
                }
            },
        },
    ],
}
