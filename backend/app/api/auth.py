"""Login. The token identifies the caller. It does not grant document access."""

import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.passwords import verify_password
from app.auth.tokens import TokenError, issue_token, read_token
from app.core.config import get_settings
from app.models.user import User
from app.repositories.users import get_by_email, get_by_id
from app.schemas.users import LoginRequest, LoginResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    cleaned = email.strip().lower()
    if _EMAIL.fullmatch(cleaned) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter a valid email",
        )
    return cleaned


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        created_at=user.created_at,
    )


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    settings = get_settings()
    try:
        payload = read_token(credentials.credentials, settings.jwt_secret)
        user_id = uuid.UUID(str(payload["sub"]))
    except (TokenError, ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required",
        ) from exc
    user = await get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    return user


async def require_super_admin(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin only")
    return user


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    email = normalize_email(body.email)
    user = await get_by_email(email)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is wrong",
        )
    settings = get_settings()
    token = issue_token(
        str(user.id),
        user.email,
        user.role,
        settings.jwt_secret,
        settings.jwt_ttl_hours * 3600,
    )
    return LoginResponse(access_token=token, user=user_response(user))


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(current_user)]) -> UserResponse:
    return user_response(user)
