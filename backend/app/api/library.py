"""Upload a document, chat with it locally, and let an admin grant access."""

import uuid
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.api.auth import current_user, require_super_admin
from app.api.chat import ConversationNotFound, choice_settings, open_conversation
from app.authz.client import OpenFGAError, get_openfga_client
from app.authz.demo import InvalidGrant
from app.documents.extract import EmptyDocument, UnsupportedFile
from app.documents.ollama_embed import EmbeddingError
from app.intent import resolve_intent
from app.knowledge import UnknownSpace, WrongSpaceFile, space_by_id
from app.models.user import User
from app.repositories.chat import add_exchange
from app.repositories.grants import DuplicateGrantError
from app.schemas.library import (
    DocumentAccess,
    LibraryAskRequest,
    LibraryAskResponse,
    LibraryDocument,
    ShareRequest,
)
from app.services.library import (
    DocumentAccessError,
    DocumentNotFound,
    access_list,
    all_documents,
    ask_document,
    documents_for,
    max_upload_bytes,
    save_upload,
    share_document,
    unshare_document,
)

router = APIRouter(tags=["library"])


def _unavailable(exc: OpenFGAError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


def _fail(code: int, detail: str, exc: Exception) -> NoReturn:
    raise HTTPException(status_code=code, detail=detail) from exc


@router.get("/library", response_model=list[LibraryDocument])
async def my_library(
    user: Annotated[User, Depends(current_user)],
    space: Annotated[str | None, Query()] = None,
) -> list[LibraryDocument]:
    if space is not None:
        try:
            space_by_id(space)
        except UnknownSpace as exc:
            _fail(status.HTTP_422_UNPROCESSABLE_ENTITY, "That knowledge space does not exist", exc)
    return await documents_for(user, space)


@router.post("/library", response_model=LibraryDocument, status_code=status.HTTP_201_CREATED)
async def upload_library_document(
    user: Annotated[User, Depends(current_user)],
    file: Annotated[UploadFile, File()],
    space: Annotated[str | None, Form()] = None,
) -> LibraryDocument:
    data = await file.read()
    if len(data) > max_upload_bytes():
        _fail(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "The file is over 20 MB", ValueError())
    try:
        document = await save_upload(
            user,
            file.filename or "upload.txt",
            file.content_type or "application/octet-stream",
            data,
            get_openfga_client(),
            space,
        )
    except UnknownSpace as exc:
        _fail(status.HTTP_422_UNPROCESSABLE_ENTITY, "That knowledge space does not exist", exc)
    except WrongSpaceFile as exc:
        _fail(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc), exc)
    except UnsupportedFile as exc:
        _fail(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc), exc)
    except EmptyDocument as exc:
        _fail(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc), exc)
    except EmbeddingError as exc:
        _fail(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc), exc)
    except OpenFGAError as exc:
        raise _unavailable(exc) from exc
    saved = await documents_for(user)
    match = next((item for item in saved if item.id == document.id), None)
    if match is None:
        _fail(status.HTTP_500_INTERNAL_SERVER_ERROR, "Upload was not saved", RuntimeError())
    return match


@router.post("/library/{document_id}/ask", response_model=LibraryAskResponse)
async def ask_library_document(
    document_id: uuid.UUID,
    body: LibraryAskRequest,
    user: Annotated[User, Depends(current_user)],
) -> LibraryAskResponse:
    try:
        model_name, chat_settings = await choice_settings(user, body.model_id)
        conversation_id, prior = await open_conversation(
            user,
            body.conversation_id,
            document_id,
            body.prompt,
        )
        intent = await resolve_intent(body.prompt, prior)
        result = await ask_document(
            user,
            document_id,
            body.prompt,
            chat_settings,
            prior,
            conversation_id,
            intent,
        )
    except ConversationNotFound as exc:
        _fail(status.HTTP_404_NOT_FOUND, "That chat was not found", exc)
    except DocumentNotFound as exc:
        _fail(status.HTTP_404_NOT_FOUND, "That document was not found", exc)
    except DocumentAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An admin has not granted this account access to that document",
        ) from exc
    answer = result.answer if result.status == "success" and result.answer else result.error_message
    await add_exchange(
        user.id,
        document_id,
        conversation_id,
        model_name,
        body.prompt,
        answer or "The model call failed.",
        result.intent,
    )
    return result


@router.get("/admin/library", response_model=list[LibraryDocument])
async def admin_library(
    _admin: Annotated[User, Depends(require_super_admin)],
) -> list[LibraryDocument]:
    return await all_documents()


@router.get("/admin/library/{document_id}/access", response_model=list[DocumentAccess])
async def admin_library_access(
    document_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_super_admin)],
) -> list[DocumentAccess]:
    try:
        return await access_list(document_id)
    except DocumentNotFound as exc:
        _fail(status.HTTP_404_NOT_FOUND, "That document was not found", exc)


@router.post("/admin/library/{document_id}/access", status_code=status.HTTP_204_NO_CONTENT)
async def grant_library_access(
    document_id: uuid.UUID,
    body: ShareRequest,
    _admin: Annotated[User, Depends(require_super_admin)],
) -> None:
    try:
        await share_document(document_id, body.user_id, get_openfga_client())
    except DocumentNotFound as exc:
        _fail(status.HTTP_404_NOT_FOUND, "That document or member was not found", exc)
    except InvalidGrant as exc:
        _fail(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc), exc)
    except DuplicateGrantError as exc:
        _fail(status.HTTP_409_CONFLICT, "That member already has access", exc)
    except OpenFGAError as exc:
        raise _unavailable(exc) from exc


@router.delete(
    "/admin/library/{document_id}/access/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_library_access(
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_super_admin)],
) -> None:
    try:
        await unshare_document(document_id, user_id, get_openfga_client())
    except DocumentNotFound as exc:
        _fail(status.HTTP_404_NOT_FOUND, "That access grant was not found", exc)
    except OpenFGAError as exc:
        raise _unavailable(exc) from exc
