"""PostgreSQL access for OpenFGA grants."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.models.access_grant import AccessGrant, AuthzState
from app.models.user import User


class DuplicateGrantError(Exception):
    """This subject already has that relation on that object."""


class GrantNotFound(Exception):
    """No grant exists with this id."""


async def grants_were_seeded() -> bool:
    async with SessionLocal() as session:
        state = await session.get(AuthzState, 1)
        return bool(state and state.grants_seeded)


async def mark_grants_seeded() -> None:
    async with SessionLocal() as session:
        state = await session.get(AuthzState, 1)
        if state is None:
            session.add(AuthzState(id=1, grants_seeded=True))
        else:
            state.grants_seeded = True
        await session.commit()


async def list_grants() -> list[AccessGrant]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(AccessGrant).order_by(AccessGrant.created_at, AccessGrant.object_id)
        )
        return list(result.scalars().all())


async def get_grant(grant_id: uuid.UUID) -> AccessGrant | None:
    async with SessionLocal() as session:
        return await session.get(AccessGrant, grant_id)


async def insert_grant(
    subject: str,
    user_id: uuid.UUID | None,
    relation: str,
    object_id: str,
) -> AccessGrant:
    grant = AccessGrant(
        id=uuid.uuid4(),
        subject=subject,
        user_id=user_id,
        relation=relation,
        object_id=object_id,
    )
    async with SessionLocal() as session:
        session.add(grant)
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise DuplicateGrantError(subject) from exc
        await session.refresh(grant)
        return grant


async def update_grant_relation(grant_id: uuid.UUID, relation: str) -> AccessGrant:
    async with SessionLocal() as session:
        grant = await session.get(AccessGrant, grant_id)
        if grant is None:
            raise GrantNotFound(str(grant_id))
        grant.relation = relation
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise DuplicateGrantError(grant.subject) from exc
        await session.refresh(grant)
        return grant


async def delete_grant(grant_id: uuid.UUID) -> AccessGrant:
    async with SessionLocal() as session:
        grant = await session.get(AccessGrant, grant_id)
        if grant is None:
            raise GrantNotFound(str(grant_id))
        removed = AccessGrant(
            id=grant.id,
            subject=grant.subject,
            user_id=grant.user_id,
            relation=grant.relation,
            object_id=grant.object_id,
        )
        await session.delete(grant)
        await session.commit()
        return removed


async def list_users_by_id() -> dict[uuid.UUID, User]:
    async with SessionLocal() as session:
        result = await session.execute(select(User))
        return {user.id: user for user in result.scalars().all()}
