"""Olist warehouse routes."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.services.olist import load_dashboard

router = APIRouter(prefix="/olist", tags=["olist"])


@router.get("/dashboard")
async def dashboard() -> dict[str, object]:
    try:
        return await load_dashboard()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="olist warehouse is unavailable",
        ) from exc
