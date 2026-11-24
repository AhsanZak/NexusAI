"""Olist warehouse routes. Analysis permission is an OpenFGA feature check."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.auth import current_user
from app.authz.client import OpenFGAError, get_openfga_client
from app.models.user import User
from app.services.access import member_can_use
from app.services.olist import load_dashboard

router = APIRouter(prefix="/olist", tags=["olist"])


async def require_analysis(user: Annotated[User, Depends(current_user)]) -> User:
    try:
        allowed = await member_can_use(user, get_openfga_client(), "feature:analysis")
    except OpenFGAError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You are signed in as a member. "
                "Analysis permission is not granted for this account."
            ),
        )
    return user


@router.get("/dashboard")
async def dashboard(_user: Annotated[User, Depends(require_analysis)]) -> dict[str, object]:
    try:
        return await load_dashboard()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="olist warehouse is unavailable",
        ) from exc
