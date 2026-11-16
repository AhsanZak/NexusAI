"""World Bank dashboard routes."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.services.worldbank import load_dashboard

router = APIRouter(prefix="/worldbank", tags=["worldbank"])


@router.get("/dashboard")
async def dashboard() -> dict[str, object]:
    try:
        return await load_dashboard()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="world bank warehouse is unavailable",
        ) from exc
