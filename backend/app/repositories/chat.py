"""Chat history and the model each person selected."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.ai.choices import DEFAULT_MODEL
from app.core.database import SessionLocal
from app.models.chat import ChatConversation, ChatMessage, ChatPreference


async def selected_model(user_id: uuid.UUID) -> str:
    async with SessionLocal() as session:
        row = await session.get(ChatPreference, user_id)
        if row is None:
            return DEFAULT_MODEL
        return row.model_id


async def save_selected_model(user_id: uuid.UUID, model_id: str) -> None:
    async with SessionLocal() as session:
        row = await session.get(ChatPreference, user_id)
        if row is None:
            session.add(ChatPreference(user_id=user_id, model_id=model_id))
        else:
            row.model_id = model_id
        await session.commit()


async def conversations_for(
    user_id: uuid.UUID,
    document_id: uuid.UUID | None,
) -> list[ChatConversation]:
    async with SessionLocal() as session:
        query = select(ChatConversation).where(ChatConversation.user_id == user_id)
        if document_id is None:
            query = query.where(ChatConversation.document_id.is_(None))
        else:
            query = query.where(ChatConversation.document_id == document_id)
        result = await session.execute(query.order_by(ChatConversation.updated_at.desc()))
        return list(result.scalars().all())


async def recent_conversations(user_id: uuid.UUID) -> list[ChatConversation]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(ChatConversation)
            .where(ChatConversation.user_id == user_id)
            .order_by(ChatConversation.updated_at.desc())
        )
        return list(result.scalars().all())


async def conversation_for(
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> ChatConversation | None:
    async with SessionLocal() as session:
        row = await session.get(ChatConversation, conversation_id)
        if row is None or row.user_id != user_id:
            return None
        return row


async def create_conversation(
    user_id: uuid.UUID,
    document_id: uuid.UUID | None,
    title: str,
    space: str | None = None,
) -> uuid.UUID:
    conversation_id = uuid.uuid4()
    async with SessionLocal() as session:
        session.add(
            ChatConversation(
                id=conversation_id,
                user_id=user_id,
                document_id=document_id,
                title=title,
                space=space,
            )
        )
        await session.commit()
    return conversation_id


async def delete_conversation(user_id: uuid.UUID, conversation_id: uuid.UUID) -> bool:
    async with SessionLocal() as session:
        row = await session.get(ChatConversation, conversation_id)
        if row is None or row.user_id != user_id:
            return False
        await session.delete(row)
        await session.commit()
    return True


async def add_exchange(
    user_id: uuid.UUID,
    document_id: uuid.UUID | None,
    conversation_id: uuid.UUID,
    model_name: str,
    question: str,
    answer: str,
    intent: str | None = None,
) -> None:
    async with SessionLocal() as session:
        conversation = await session.get(ChatConversation, conversation_id)
        session.add(
            ChatMessage(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                user_id=user_id,
                document_id=document_id,
                model_name=model_name,
                role="user",
                intent=intent,
                content=question,
            )
        )
        session.add(
            ChatMessage(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                user_id=user_id,
                document_id=document_id,
                model_name=model_name,
                role="assistant",
                content=answer,
            )
        )
        if conversation is not None:
            conversation.updated_at = datetime.now(UTC)
            conversation.intent = intent
        await session.commit()


async def messages_for(conversation_id: uuid.UUID) -> list[ChatMessage]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at)
        )
        return list(result.scalars().all())
