"""Copy PostgreSQL grants into OpenFGA and answer Check for the signed-in account."""

import uuid
from dataclasses import dataclass
from typing import Literal

from app.authz.client import OpenFGAClient
from app.authz.demo import (
    DOCUMENT_RELATIONS,
    DOCUMENTS,
    FEATURES,
    GUEST_SUBJECT,
    InvalidGrant,
    member_subject,
    object_name,
    object_type,
    validate_grant,
)
from app.models.access_grant import AccessGrant
from app.models.user import User
from app.repositories.grants import (
    DuplicateGrantError,
    GrantNotFound,
    delete_grant,
    get_grant,
    grants_were_seeded,
    insert_grant,
    list_grants,
    list_users_by_id,
    mark_grants_seeded,
    update_grant_relation,
)
from app.repositories.users import get_by_email, get_by_id
from app.schemas.access import (
    AssignmentView,
    CatalogItem,
    DocumentView,
    FeatureView,
    GrantResponse,
    MyAccessResponse,
    PermissionListResponse,
)

# Applied once. Later admin deletes stay deleted.
_DEFAULTS: dict[str, tuple[tuple[str, str], ...]] = {
    "amina@nexusai.local": (
        ("viewer", "document:world-bank"),
        ("analyst", "document:olist-sales"),
        ("can_use", "feature:ai-model"),
        ("can_use", "feature:analysis"),
    ),
    "luis@nexusai.local": (
        ("viewer", "document:world-bank"),
        ("auditor", "document:finance-reviews"),
        ("can_use", "feature:ai-model"),
    ),
}


@dataclass(frozen=True)
class _Resolved:
    subject: str
    user_id: uuid.UUID | None


def catalog() -> list[CatalogItem]:
    items = [
        CatalogItem(
            object_id=document.object_id,
            name=document.name,
            object_type="document",
            releasing_relation=document.relation,
            relations=list(DOCUMENT_RELATIONS),
        )
        for document in DOCUMENTS
    ]
    items.extend(
        CatalogItem(
            object_id=feature.object_id,
            name=feature.name,
            object_type="feature",
            releasing_relation=feature.relation,
            relations=["can_use"],
        )
        for feature in FEATURES
    )
    return items


async def ensure_default_grants() -> None:
    """Insert the starting member grants the first time this database is used."""
    if await grants_were_seeded():
        return
    for email, pairs in _DEFAULTS.items():
        user = await get_by_email(email)
        if user is None:
            continue
        subject = member_subject(user.id)
        for relation, object_id in pairs:
            try:
                await insert_grant(subject, user.id, relation, object_id)
            except DuplicateGrantError:
                continue
    await mark_grants_seeded()


async def sync_grants(client: OpenFGAClient) -> list[AccessGrant]:
    """Write every stored grant into OpenFGA. Check then sees the admin's latest rows."""
    await ensure_default_grants()
    grants = await list_grants()
    await client.prepare()
    await client.write_tuples([(item.subject, item.relation, item.object_id) for item in grants])
    return grants


async def list_permissions(client: OpenFGAClient) -> PermissionListResponse:
    grants = await sync_grants(client)
    users = await list_users_by_id()
    return PermissionListResponse(
        catalog=catalog(),
        grants=[
            _grant_response(item, users)
            for item in grants
            if not item.object_id.startswith("document:upload-")
        ],
    )


async def create_permission(
    client: OpenFGAClient,
    subject_kind: str,
    user_id: uuid.UUID | None,
    relation: str,
    object_id: str,
) -> GrantResponse:
    await ensure_default_grants()
    validate_grant(object_id, relation)
    resolved = await _resolve(subject_kind, user_id)
    grant = await insert_grant(resolved.subject, resolved.user_id, relation, object_id)
    try:
        await sync_grants(client)
    except Exception:
        await delete_grant(grant.id)
        raise
    users = await list_users_by_id()
    return _grant_response(grant, users)


async def update_permission(
    client: OpenFGAClient,
    grant_id: uuid.UUID,
    relation: str,
) -> GrantResponse:
    current = await get_grant(grant_id)
    if current is None:
        raise GrantNotFound(str(grant_id))
    validate_grant(current.object_id, relation)
    previous = (current.subject, current.relation, current.object_id)
    if relation == current.relation:
        users = await list_users_by_id()
        return _grant_response(current, users)
    updated = await update_grant_relation(grant_id, relation)
    try:
        await client.prepare()
        await client.delete_tuples([previous])
        await sync_grants(client)
    except Exception:
        await update_grant_relation(grant_id, previous[1])
        raise
    users = await list_users_by_id()
    return _grant_response(updated, users)


async def delete_permission(client: OpenFGAClient, grant_id: uuid.UUID) -> None:
    current = await get_grant(grant_id)
    if current is None:
        raise GrantNotFound(str(grant_id))
    previous = (current.subject, current.relation, current.object_id)
    await delete_grant(grant_id)
    try:
        await client.prepare()
        await client.delete_tuples([previous])
    except Exception:
        await insert_grant(current.subject, current.user_id, current.relation, current.object_id)
        raise


async def my_access(user: User, client: OpenFGAClient) -> MyAccessResponse:
    """Check the signed-in account and, separately, the guest subject."""
    grants = await sync_grants(client)
    actor: Literal["member", "super_admin"] = (
        "super_admin" if user.role == "super_admin" else "member"
    )
    subject = member_subject(user.id)
    features: list[FeatureView] = []
    for feature in FEATURES:
        allowed = actor == "super_admin" or await client.check(
            subject,
            feature.relation,
            feature.object_id,
        )
        features.append(
            FeatureView(object_id=feature.object_id, name=feature.name, allowed=allowed)
        )
    documents: list[DocumentView] = []
    for document in DOCUMENTS:
        allowed = await client.check(subject, document.relation, document.object_id)
        guest_allowed = await client.check(GUEST_SUBJECT, document.relation, document.object_id)
        documents.append(
            DocumentView(
                object_id=document.object_id,
                object_name=document.name,
                relation=document.relation,
                actor=actor,
                allowed=allowed,
                guest_allowed=guest_allowed,
                content=document.content if allowed else None,
            )
        )
    return MyAccessResponse(
        actor=actor,
        subject=subject,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        features=features,
        documents=documents,
        assignments=[_assignment(item) for item in grants if item.subject == subject],
        guest_assignments=[_assignment(item) for item in grants if item.subject == GUEST_SUBJECT],
    )


async def member_can_use(user: User, client: OpenFGAClient, feature_id: str) -> bool:
    await sync_grants(client)
    if user.role == "super_admin":
        return True
    return await client.check(member_subject(user.id), "can_use", feature_id)


async def _resolve(subject_kind: str, user_id: uuid.UUID | None) -> _Resolved:
    if subject_kind == "guest":
        return _Resolved(GUEST_SUBJECT, None)
    if subject_kind != "member" or user_id is None:
        raise InvalidGrant("Choose a member or the guest")
    user = await get_by_id(user_id)
    if user is None:
        raise GrantNotFound(str(user_id))
    return _Resolved(member_subject(user.id), user.id)


def _grant_response(grant: AccessGrant, users: dict[uuid.UUID, User]) -> GrantResponse:
    actor: Literal["member", "guest"]
    if grant.subject == GUEST_SUBJECT:
        actor = "guest"
        display_name = "Guest"
        email = None
    else:
        actor = "member"
        user = users.get(grant.user_id) if grant.user_id else None
        display_name = user.display_name if user else grant.subject
        email = user.email if user else None
    return GrantResponse(
        id=grant.id,
        subject=grant.subject,
        actor=actor,
        user_id=grant.user_id,
        display_name=display_name,
        email=email,
        relation=grant.relation,
        object_id=grant.object_id,
        object_name=object_name(grant.object_id),
        object_type=object_type(grant.object_id),
        created_at=grant.created_at,
    )


def _assignment(grant: AccessGrant) -> AssignmentView:
    return AssignmentView(
        relation=grant.relation,
        object_id=grant.object_id,
        object_name=object_name(grant.object_id),
        object_type=object_type(grant.object_id),
        actor="guest" if grant.subject == GUEST_SUBJECT else "member",
    )
