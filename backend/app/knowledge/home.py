"""Counts and chats for the dashboard a person sees after login."""

from app.intent import label_for
from app.knowledge.spaces import SPACES, UnknownSpace, space_by_id
from app.models.user import User
from app.repositories.chat import recent_conversations
from app.repositories.uploads import list_documents
from app.schemas.knowledge import KnowledgeConversation, KnowledgeHome, KnowledgeSpaceCard


async def knowledge_home(user: User) -> KnowledgeHome:
    documents = await list_documents()
    conversations = await recent_conversations(user.id)
    owned = [item for item in documents if item.owner_id == user.id]
    names = {item.id: item.filename for item in documents}
    document_counts = {item.id: 0 for item in SPACES}
    conversation_counts = {item.id: 0 for item in SPACES}
    for document in owned:
        if document.space in document_counts:
            document_counts[document.space] += 1
    for conversation in conversations:
        if conversation.space in conversation_counts:
            conversation_counts[conversation.space] += 1
    cards = [
        KnowledgeSpaceCard(
            id=space.id,
            label=space.label,
            summary=space.summary,
            placeholder=space.placeholder,
            extensions=list(space.extensions),
            document_count=document_counts[space.id],
            conversation_count=conversation_counts[space.id],
        )
        for space in SPACES
    ]
    history = [
        KnowledgeConversation(
            id=conversation.id,
            title=conversation.title,
            space=conversation.space,
            space_label=_label(conversation.space),
            document_id=conversation.document_id,
            filename=names.get(conversation.document_id) if conversation.document_id else None,
            intent_label=label_for(conversation.intent),
            updated_at=conversation.updated_at,
        )
        for conversation in conversations
    ]
    return KnowledgeHome(spaces=cards, conversations=history)


def _label(space_id: str | None) -> str:
    if space_id is None:
        return "Assistant"
    try:
        return space_by_id(space_id).label
    except UnknownSpace:
        return "Assistant"
