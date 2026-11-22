"""Two demo users, one shared permission, and one permission each."""

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
    ],
}
