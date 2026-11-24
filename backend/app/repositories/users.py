"""PostgreSQL access for login accounts."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth.passwords import hash_password
from app.core.database import SessionLocal
from app.models.user import User


class DuplicateEmailError(Exception):
    """An account with this email already exists."""


async def get_by_email(email: str) -> User | None:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


async def get_by_id(user_id: uuid.UUID) -> User | None:
    async with SessionLocal() as session:
        return await session.get(User, user_id)


async def list_users() -> list[User]:
    async with SessionLocal() as session:
        result = await session.execute(select(User).order_by(User.created_at))
        return list(result.scalars().all())


async def create_user(email: str, display_name: str, password: str, role: str) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        display_name=display_name,
        password_hash=hash_password(password),
        role=role,
    )
    async with SessionLocal() as session:
        session.add(user)
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise DuplicateEmailError(email) from exc
        await session.refresh(user)
        return user
