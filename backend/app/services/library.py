"""Save an upload, retrieve its chunks, and chat through the Ollama GPU server."""

import base64
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from app.ai.gateway import LLMCallError, complete
from app.authz.client import OpenFGAClient
from app.authz.demo import member_subject
from app.core.config import Settings, get_settings
from app.documents.extract import ExtractedDocument, extract_upload
from app.documents.ollama_embed import EmbeddingError, embed_texts
from app.documents.vectors import chunk_text, rank_by_vector, rank_chunks
from app.intent import UserIntent, apply_intent, classify_intent
from app.knowledge import infer_space, require_file
from app.models.access_grant import AccessGrant
from app.models.upload import DocumentChunk, UploadedDocument
from app.models.user import User
from app.repositories.grants import list_grants, list_users_by_id
from app.repositories.uploads import (
    chunks_for,
    get_document,
    insert_chunks,
    insert_document,
    list_documents,
    replace_chunks,
)
from app.repositories.users import get_by_id
from app.schemas.library import DocumentAccess, LibraryAskResponse, LibraryDocument, LibraryExcerpt
from app.services.access import create_permission, delete_permission
from app.services.chat_context import append_prior

_MAX_BYTES = 20 * 1024 * 1024
_FULL_TEXT_CHARS = 12000
_IMAGE_BYTES = 8 * 1024 * 1024
_EMBEDDING = "bge-m3"
_IMAGE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".bmp": "image/bmp",
    ".gif": "image/gif",
}


class DocumentAccessError(Exception):
    """This account is not allowed to read the uploaded document."""


class DocumentNotFound(Exception):
    """No uploaded document has this id."""


def upload_object(document_id: uuid.UUID) -> str:
    return f"document:upload-{document_id}"


def can_view(user: User, document: UploadedDocument, granted_user_ids: set[uuid.UUID]) -> bool:
    """The owner and a super admin can read it. Another member needs an admin grant."""
    if user.role == "super_admin" or user.id == document.owner_id:
        return True
    return user.id in granted_user_ids


def max_upload_bytes() -> int:
    return _MAX_BYTES


async def save_upload(
    owner: User,
    filename: str,
    media_type: str,
    data: bytes,
    client: OpenFGAClient,
    space: str | None = None,
) -> UploadedDocument:
    safe_name = Path(filename).name.strip() or "upload.txt"
    space_id = require_file(space, safe_name).id if space else infer_space(safe_name)
    extracted = _extract_for_space(space_id, safe_name, data)
    pieces = chunk_text(extracted.text)
    settings = get_settings()
    vectors = await embed_texts(
        pieces,
        base_url=settings.ollama_base_url,
        model=settings.ollama_embed_model,
    )
    suffix = Path(safe_name).suffix.lower()
    storage_name = f"{uuid.uuid4().hex}{suffix}"
    folder = _upload_dir()
    (folder / storage_name).write_bytes(data)
    document = await insert_document(
        owner.id,
        safe_name,
        media_type or "application/octet-stream",
        storage_name,
        extracted.text,
        extracted.extractor,
        _EMBEDDING,
        space_id,
    )
    await insert_chunks(
        document.id,
        [
            (index, content, vector)
            for index, (content, vector) in enumerate(zip(pieces, vectors, strict=True))
        ],
    )
    await create_permission(
        client,
        "member",
        owner.id,
        "viewer",
        upload_object(document.id),
    )
    return document


async def documents_for(user: User, space: str | None = None) -> list[LibraryDocument]:
    documents = await list_documents()
    grants = await list_grants()
    users = await list_users_by_id()
    visible: list[LibraryDocument] = []
    for document in documents:
        if space is not None and document.space != space:
            continue
        granted = _granted_users(grants, document.id)
        if not can_view(user, document, granted):
            continue
        owner = users.get(document.owner_id)
        shared = user.id != document.owner_id and user.role != "super_admin"
        visible.append(_library_document(document, owner, shared))
    return visible


async def all_documents() -> list[LibraryDocument]:
    documents = await list_documents()
    users = await list_users_by_id()
    return [
        _library_document(document, users.get(document.owner_id), shared=False)
        for document in documents
    ]


async def access_list(document_id: uuid.UUID) -> list[DocumentAccess]:
    document = await get_document(document_id)
    if document is None:
        raise DocumentNotFound(str(document_id))
    users = await list_users_by_id()
    rows: list[DocumentAccess] = []
    owner = users.get(document.owner_id)
    if owner is not None:
        rows.append(
            DocumentAccess(
                user_id=owner.id,
                display_name=owner.display_name,
                email=owner.email,
                owner=True,
            )
        )
    for grant in await list_grants():
        owner_or_other = grant.user_id in {None, document.owner_id}
        if grant.object_id != upload_object(document_id) or owner_or_other:
            continue
        member = users.get(grant.user_id) if grant.user_id else None
        if member is None:
            continue
        rows.append(
            DocumentAccess(
                user_id=member.id,
                display_name=member.display_name,
                email=member.email,
                owner=False,
            )
        )
    return rows


async def share_document(
    document_id: uuid.UUID,
    member_id: uuid.UUID,
    client: OpenFGAClient,
) -> None:
    document = await get_document(document_id)
    member = await get_by_id(member_id)
    if document is None or member is None:
        raise DocumentNotFound(str(document_id))
    if member.id == document.owner_id:
        return
    await create_permission(client, "member", member.id, "viewer", upload_object(document.id))


async def unshare_document(
    document_id: uuid.UUID,
    member_id: uuid.UUID,
    client: OpenFGAClient,
) -> None:
    target = upload_object(document_id)
    subject = member_subject(member_id)
    for grant in await list_grants():
        if grant.object_id == target and grant.subject == subject:
            await delete_permission(client, grant.id)
            return
    raise DocumentNotFound(str(document_id))


async def ensure_can_view(user: User, document_id: uuid.UUID) -> None:
    document = await get_document(document_id)
    if document is None:
        raise DocumentNotFound(str(document_id))
    granted = _granted_users(await list_grants(), document.id)
    if not can_view(user, document, granted):
        raise DocumentAccessError(document.filename)


async def ask_document(
    user: User,
    document_id: uuid.UUID,
    question: str,
    chat_settings: Settings | None = None,
    prior: list[dict[str, str]] | None = None,
    conversation_id: uuid.UUID | None = None,
    intent: UserIntent | None = None,
) -> LibraryAskResponse:
    document = await get_document(document_id)
    if document is None:
        raise DocumentNotFound(str(document_id))
    granted = _granted_users(await list_grants(), document.id)
    if not can_view(user, document, granted):
        raise DocumentAccessError(document.filename)
    retrieval = get_settings()
    intent = intent or classify_intent(question, prior)
    chat = (chat_settings or retrieval).model_copy(update={"llm_timeout_seconds": 180})
    if intent.needs_documents:
        stored = await _current_chunks(document, retrieval)
        ranked = await _rank(question, document, stored, retrieval)
        excerpts = _excerpts_for(document, stored, ranked)
        prepared = append_prior(_messages(document, excerpts, question), prior or [])
    else:
        excerpts = []
        prepared = append_prior(
            [
                {
                    "role": "system",
                    "content": (
                        "Answer the user's question directly. "
                        "Do not search the uploaded document and do not say it is missing "
                        "the answer. "
                        "Use earlier turns in this chat when the question refers to them."
                    ),
                },
                {"role": "user", "content": question},
            ],
            prior or [],
        )
    messages = apply_intent(prepared, intent)
    try:
        trace = await complete(messages, source="document-chat", settings=chat, temperature=0)
    except LLMCallError as exc:
        trace = exc.trace
    return LibraryAskResponse(
        conversation_id=conversation_id or document.id,
        document_id=document.id,
        intent=intent.name,
        intent_label=intent.label,
        filename=document.filename,
        status=trace.status,
        answer=trace.response_text,
        error_message=trace.error_message,
        excerpts=excerpts,
    )


def _messages(
    document: UploadedDocument,
    excerpts: list[LibraryExcerpt],
    question: str,
) -> list[dict[str, Any]]:
    body = "\n\n".join(f"Excerpt {item.chunk_index + 1}:\n{item.content}" for item in excerpts)
    system = (
        "The question asks about the uploaded document. "
        "Copy numbers, names, dates, and table cells exactly as written. "
        "When an image is attached, use it to correct text the excerpts missed. "
        "If several rows match, include each row. "
        "If the document does not contain the answer, say that. "
        "Do not invent rows, numbers, or names.\n\n"
        f"Document: {document.filename}\n\n{body or 'None.'}"
    )
    image = _image_part(document)
    user: Any = question if image is None else [{"type": "text", "text": question}, image]
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


async def _current_chunks(document: UploadedDocument, settings: Settings) -> list[DocumentChunk]:
    stored = await chunks_for(document.id)
    fresh = chunk_text(document.extracted_text)
    if document.embedding_kind == _EMBEDDING and [chunk.content for chunk in stored] == fresh:
        return stored
    if not fresh:
        return stored
    try:
        vectors = await embed_texts(
            fresh,
            base_url=settings.ollama_base_url,
            model=settings.ollama_embed_model,
        )
    except EmbeddingError:
        return stored
    paired = enumerate(zip(fresh, vectors, strict=True))
    await replace_chunks(
        document.id,
        _EMBEDDING,
        [(index, content, vector) for index, (content, vector) in paired],
    )
    document.embedding_kind = _EMBEDDING
    return await chunks_for(document.id)


def _excerpts_for(
    document: UploadedDocument,
    stored: list[DocumentChunk],
    ranked: list[int],
) -> list[LibraryExcerpt]:
    """Short files are sent whole. Longer files send the bge-m3 matches, best first."""
    full = document.extracted_text.strip()
    if full and len(full) <= _FULL_TEXT_CHARS:
        return [LibraryExcerpt(chunk_index=0, content=full)]
    by_index = {chunk.chunk_index: chunk for chunk in stored}
    return [
        LibraryExcerpt(chunk_index=index, content=by_index[index].content)
        for index in ranked
        if index in by_index
    ]


async def _rank(
    question: str,
    document: UploadedDocument,
    stored: list[DocumentChunk],
    settings: Settings,
) -> list[int]:
    rows = [(chunk.chunk_index, chunk.content, list(chunk.embedding)) for chunk in stored]
    if document.embedding_kind != _EMBEDDING:
        return rank_chunks(question, rows, limit=6)
    try:
        embedded = await embed_texts(
            [question],
            base_url=settings.ollama_base_url,
            model=settings.ollama_embed_model,
        )
    except EmbeddingError:
        return [index for index, _content, _vector in rows][:6]
    return rank_by_vector(embedded[0], rows, limit=6)


def _granted_users(grants: Sequence[AccessGrant], document_id: uuid.UUID) -> set[uuid.UUID]:
    target = upload_object(document_id)
    return {
        grant.user_id
        for grant in grants
        if grant.object_id == target and grant.user_id is not None
    }


def _library_document(
    document: UploadedDocument,
    owner: User | None,
    shared: bool,
) -> LibraryDocument:
    excerpt = document.extracted_text.strip().replace("\n", " ")
    if len(excerpt) > 240:
        excerpt = excerpt[:240] + "…"
    return LibraryDocument(
        id=document.id,
        filename=document.filename,
        space=document.space,
        media_type=document.media_type,
        extractor=document.extractor,
        embedding_kind=document.embedding_kind,
        owner_id=document.owner_id,
        owner_name=owner.display_name if owner else "Unknown",
        owner_email=owner.email if owner else "",
        shared=shared,
        excerpt=excerpt,
        created_at=document.created_at,
    )


def _extract_for_space(space_id: str, filename: str, data: bytes) -> ExtractedDocument:
    if space_id == "video":
        return ExtractedDocument(
            f"Video file {filename}. The frames were not read, so use only this file name.",
            "stored",
        )
    return extract_upload(filename, data)


def _image_part(document: UploadedDocument) -> dict[str, Any] | None:
    media = _IMAGE_TYPES.get(Path(document.filename).suffix.lower())
    if media is None:
        return None
    path = _upload_dir() / document.storage_name
    if not path.is_file() or path.stat().st_size > _IMAGE_BYTES:
        return None
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{media};base64,{encoded}"}}


def _upload_dir() -> Path:
    folder = Path(__file__).resolve().parents[3] / "data" / "documents" / "uploads"
    folder.mkdir(parents=True, exist_ok=True)
    return folder
