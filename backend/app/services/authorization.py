"""Service-layer OpenFGA checks. Document text is added only after an allow."""

from dataclasses import dataclass

from app.authz.client import PermissionChecker
from app.authz.demo import DOCUMENTS, USERS


@dataclass(frozen=True)
class AccessDecision:
    user_id: str
    display_name: str
    role: str
    relation: str
    object_id: str
    object_name: str
    shared: bool
    allowed: bool
    content: str | None


async def collect_decisions(checker: PermissionChecker) -> list[AccessDecision]:
    """Ask OpenFGA once per user and document. Denied rows carry no document text."""
    allowed_by_key: dict[tuple[str, str, str], bool] = {}
    for user in USERS:
        for document in DOCUMENTS:
            key = (user.user_id, document.relation, document.object_id)
            allowed_by_key[key] = await checker.check(
                user.user_id,
                document.relation,
                document.object_id,
            )

    decisions: list[AccessDecision] = []
    for user in USERS:
        for document in DOCUMENTS:
            allowed = allowed_by_key[(user.user_id, document.relation, document.object_id)]
            shared = all(
                allowed_by_key[(candidate.user_id, document.relation, document.object_id)]
                for candidate in USERS
            )
            decisions.append(
                AccessDecision(
                    user_id=user.user_id,
                    display_name=user.display_name,
                    role=user.role,
                    relation=document.relation,
                    object_id=document.object_id,
                    object_name=document.name,
                    shared=shared,
                    allowed=allowed,
                    content=document.content if allowed else None,
                )
            )
    return decisions
