"""PostgreSQL access for uploaded documents and their chunks."""

import uuid

from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.upload import DocumentChunk, UploadedDocument


async def insert_document(
    owner_id: uuid.UUID,
    filename: str,
    media_type: str,
    storage_name: str,
    extracted_text: str,
    extractor: str,
    embedding_kind: str,
    space: str,
) -> UploadedDocument:
    document = UploadedDocument(
        id=uuid.uuid4(),
        owner_id=owner_id,
        filename=filename,
        space=space,
        media_type=media_type,
        storage_name=storage_name,
        extracted_text=extracted_text,
        extractor=extractor,
        embedding_kind=embedding_kind,
    )
    async with SessionLocal() as session:
        session.add(document)
        await session.commit()
        await session.refresh(document)
        return document


async def insert_chunks(
    document_id: uuid.UUID,
    chunks: list[tuple[int, str, list[float]]],
) -> None:
    async with SessionLocal() as session:
        for index, content, embedding in chunks:
            session.add(
                DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    chunk_index=index,
                    content=content,
                    embedding=embedding,
                )
            )
        await session.commit()


async def list_documents() -> list[UploadedDocument]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(UploadedDocument).order_by(UploadedDocument.created_at.desc())
        )
        return list(result.scalars().all())


async def get_document(document_id: uuid.UUID) -> UploadedDocument | None:
    async with SessionLocal() as session:
        return await session.get(UploadedDocument, document_id)


async def delete_document(document_id: uuid.UUID) -> str | None:
    """Remove the document row. Chunks and chats that point at it are removed too."""
    async with SessionLocal() as session:
        document = await session.get(UploadedDocument, document_id)
        if document is None:
            return None
        storage_name = document.storage_name
        await session.delete(document)
        await session.commit()
        return storage_name


async def save_embeddings(
    document_id: uuid.UUID,
    embedding_kind: str,
    vectors: dict[int, list[float]],
) -> None:
    async with SessionLocal() as session:
        document = await session.get(UploadedDocument, document_id)
        if document is None:
            return
        document.embedding_kind = embedding_kind
        result = await session.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        for chunk in result.scalars().all():
            vector = vectors.get(chunk.chunk_index)
            if vector is not None:
                chunk.embedding = vector
        await session.commit()


async def replace_chunks(
    document_id: uuid.UUID,
    embedding_kind: str,
    chunks: list[tuple[int, str, list[float]]],
) -> None:
    async with SessionLocal() as session:
        document = await session.get(UploadedDocument, document_id)
        if document is None:
            return
        document.embedding_kind = embedding_kind
        await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        for index, content, embedding in chunks:
            session.add(
                DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    chunk_index=index,
                    content=content,
                    embedding=embedding,
                )
            )
        await session.commit()


async def chunks_for(document_id: uuid.UUID) -> list[DocumentChunk]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return list(result.scalars().all())
