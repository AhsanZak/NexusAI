"""What the signed-in account can open. Guest is checked as a separate subject."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import current_user
from app.authz.client import OpenFGAError, get_openfga_client
from app.models.user import User
from app.schemas.access import MyAccessResponse
from app.services.access import my_access

router = APIRouter(prefix="/access", tags=["access"])


@router.get("/me", response_model=MyAccessResponse)
async def read_my_access(user: Annotated[User, Depends(current_user)]) -> MyAccessResponse:
    try:
        return await my_access(user, get_openfga_client())
    except OpenFGAError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
