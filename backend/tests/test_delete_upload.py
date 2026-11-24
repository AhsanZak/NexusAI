"""Deleting a chat's file removes the stored upload and refuses someone else's file."""

import uuid
from pathlib import Path

import pytest

from app.authz.client import OpenFGAError
from app.models.user import User
from app.services import library
from app.services.library import DocumentOwnerError, delete_upload


def _user(user_id: uuid.UUID) -> User:
    return User(
        id=user_id,
        email="owner@nexusai.local",
        display_name="Owner",
        password_hash="x",
        role="member",
    )


class _Document:
    def __init__(self, document_id: uuid.UUID, owner_id: uuid.UUID, storage_name: str) -> None:
        self.id = document_id
        self.owner_id = owner_id
        self.filename = "notes.txt"
        self.storage_name = storage_name


class _Grant:
    def __init__(self, document_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.id = uuid.uuid4()
        self.subject = f"user:{user_id}"
        self.user_id = user_id
        self.relation = "viewer"
        self.object_id = f"document:upload-{document_id}"


class _Client:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.tuples: list[tuple[str, str, str]] = []

    async def prepare(self) -> None:
        return None

    async def delete_tuples(self, tuples: list[tuple[str, str, str]]) -> None:
        if self.fail:
            raise OpenFGAError("down")
        self.tuples = tuples


@pytest.mark.asyncio
async def test_owner_delete_removes_the_file_and_grant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_id = uuid.uuid4()
    document_id = uuid.uuid4()
    storage_name = "abc123.txt"
    (tmp_path / storage_name).write_text("hello", encoding="utf-8")
    grant = _Grant(document_id, owner_id)
    deleted: dict[str, uuid.UUID] = {}
    restored: list[str] = []

    async def get_document(document: uuid.UUID) -> _Document:
        assert document == document_id
        return _Document(document_id, owner_id, storage_name)

    async def list_grants() -> list[_Grant]:
        return [grant]

    async def delete_grant(grant_id: uuid.UUID) -> _Grant:
        deleted["grant"] = grant_id
        return grant

    async def insert_grant(*_args: object) -> None:
        restored.append("restored")

    async def delete_document(document: uuid.UUID) -> str:
        deleted["document"] = document
        return storage_name

    monkeypatch.setattr(library, "get_document", get_document)
    monkeypatch.setattr(library, "list_grants", list_grants)
    monkeypatch.setattr(library, "delete_grant", delete_grant)
    monkeypatch.setattr(library, "insert_grant", insert_grant)
    monkeypatch.setattr(library, "delete_document", delete_document)
    monkeypatch.setattr(library, "_upload_dir", lambda: tmp_path)

    client = _Client()
    await delete_upload(_user(owner_id), document_id, client)  # type: ignore[arg-type]
    assert deleted["document"] == document_id
    assert deleted["grant"] == grant.id
    assert not (tmp_path / storage_name).exists()
    assert client.tuples == [(grant.subject, grant.relation, grant.object_id)]
    assert restored == []


@pytest.mark.asyncio
async def test_someone_else_cannot_delete_the_file(monkeypatch: pytest.MonkeyPatch) -> None:
    owner_id = uuid.uuid4()
    document_id = uuid.uuid4()

    async def get_document(_document: uuid.UUID) -> _Document:
        return _Document(document_id, owner_id, "abc.txt")

    monkeypatch.setattr(library, "get_document", get_document)
    with pytest.raises(DocumentOwnerError):
        await delete_upload(_user(uuid.uuid4()), document_id, _Client())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_access_failure_keeps_the_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_id = uuid.uuid4()
    document_id = uuid.uuid4()
    storage_name = "keep.txt"
    (tmp_path / storage_name).write_text("keep", encoding="utf-8")
    grant = _Grant(document_id, owner_id)
    restored: list[tuple[object, ...]] = []
    deleted_documents: list[uuid.UUID] = []

    async def get_document(_document: uuid.UUID) -> _Document:
        return _Document(document_id, owner_id, storage_name)

    async def list_grants() -> list[_Grant]:
        return [grant]

    async def delete_grant(_grant_id: uuid.UUID) -> _Grant:
        return grant

    async def insert_grant(*args: object) -> None:
        restored.append(args)

    async def delete_document(document: uuid.UUID) -> str:
        deleted_documents.append(document)
        return storage_name

    monkeypatch.setattr(library, "get_document", get_document)
    monkeypatch.setattr(library, "list_grants", list_grants)
    monkeypatch.setattr(library, "delete_grant", delete_grant)
    monkeypatch.setattr(library, "insert_grant", insert_grant)
    monkeypatch.setattr(library, "delete_document", delete_document)
    monkeypatch.setattr(library, "_upload_dir", lambda: tmp_path)

    with pytest.raises(OpenFGAError):
        await delete_upload(_user(owner_id), document_id, _Client(fail=True))  # type: ignore[arg-type]
    assert (tmp_path / storage_name).exists()
    assert deleted_documents == []
    assert restored == [(grant.subject, grant.user_id, grant.relation, grant.object_id)]
