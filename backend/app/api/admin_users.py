"""Super-admin user management. Accounts are rows in PostgreSQL."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import normalize_email, require_super_admin, user_response
from app.models.user import User
from app.repositories.users import DuplicateEmailError, create_user, list_users
from app.schemas.users import CreateUserRequest, UserResponse

router = APIRouter(prefix="/admin/users", tags=["admin"])
_ROLES = {"member", "super_admin"}


@router.get("", response_model=list[UserResponse])
async def users(_admin: Annotated[User, Depends(require_super_admin)]) -> list[UserResponse]:
    return [user_response(user) for user in await list_users()]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def add_user(
    body: CreateUserRequest,
    _admin: Annotated[User, Depends(require_super_admin)],
) -> UserResponse:
    if body.role not in _ROLES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown role")
    try:
        user = await create_user(
            normalize_email(body.email),
            body.display_name.strip(),
            body.password,
            body.role,
        )
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That email is already registered",
        ) from exc
    return user_response(user)
