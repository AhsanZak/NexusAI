"""Dashboard of knowledge spaces and the chats that belong to them."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.auth import current_user
from app.knowledge.home import knowledge_home
from app.models.user import User
from app.schemas.knowledge import KnowledgeHome

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("", response_model=KnowledgeHome)
async def knowledge_dashboard(user: Annotated[User, Depends(current_user)]) -> KnowledgeHome:
    return await knowledge_home(user)
