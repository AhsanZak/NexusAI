"""Extraction keeps table cells, and another member cannot read a file without a grant."""

import io
import uuid

import pytest
from docx import Document
from openpyxl import Workbook

from app.documents.extract import extract_upload, markdown_table
from app.documents.vectors import chunk_text, rank_chunks, term_vector
from app.models.access_grant import AccessGrant
from app.models.user import User
from app.services import library
from app.services.library import allowed_by_openfga, can_view


def test_markdown_table_keeps_every_cell() -> None:
    rendered = markdown_table([["City", "Orders"], ["Berlin", 3], ["Lima", None]])
    assert "| City | Orders |" in rendered
    assert "| Berlin | 3 |" in rendered
    assert "| Lima |  |" in rendered


def test_word_and_excel_keep_paragraphs_and_rows() -> None:
    document = Document()
    document.add_paragraph("Quarterly note")
    table = document.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Item"
    table.rows[0].cells[1].text = "Count"
    table.rows[1].cells[0].text = "Widgets"
    table.rows[1].cells[1].text = "9"
    word_buffer = io.BytesIO()
    document.save(word_buffer)
    word = extract_upload("notes.docx", word_buffer.getvalue())
    assert "Quarterly note" in word.text
    assert "| Widgets | 9 |" in word.text

    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Sales"
    sheet.append(["Region", "Revenue"])
    sheet.append(["North", 42])
    excel_buffer = io.BytesIO()
    workbook.save(excel_buffer)
    excel = extract_upload("sales.xlsx", excel_buffer.getvalue())
    assert "## Sales" in excel.text
    assert "| North | 42 |" in excel.text


def test_a_table_stays_together_when_prose_is_split() -> None:
    table = markdown_table([["Region", "Revenue"], ["North", 42], ["South", 7]])
    chunks = chunk_text(f"Notes about the year.\n\n## Sales\n{table}", size=40)
    sales = next(chunk for chunk in chunks if "North" in chunk)
    assert "| North | 42 |" in sales
    assert "| South | 7 |" in sales
    assert "Notes about the year." not in sales


def test_retrieval_selects_the_chunk_that_mentions_the_question() -> None:
    text = "Apples are red.\n\nThe warehouse code is ZX-44.\n\nBananas are yellow."
    chunks = chunk_text(text, size=40)
    vectors = [(index, content, term_vector(content)) for index, content in enumerate(chunks)]
    chosen = rank_chunks("What is the warehouse code?", vectors)
    assert chunks[chosen[0]] == "The warehouse code is ZX-44."


def test_another_member_needs_an_admin_grant() -> None:
    owner_id = uuid.uuid4()
    member_id = uuid.uuid4()
    owner = User(
        id=owner_id,
        email="owner@nexusai.local",
        display_name="Owner",
        password_hash="x",
        role="member",
    )
    member = User(
        id=member_id,
        email="member@nexusai.local",
        display_name="Member",
        password_hash="x",
        role="member",
    )
    admin = User(
        id=uuid.uuid4(),
        email="admin@nexusai.local",
        display_name="Admin",
        password_hash="x",
        role="super_admin",
    )
    document_owner = owner_id

    class _Doc:
        owner_id = document_owner

    assert can_view(owner, _Doc(), set()) is True
    assert can_view(member, _Doc(), set()) is False
    assert can_view(member, _Doc(), {member_id}) is True
    assert can_view(admin, _Doc(), set()) is True


class _Checker:
    def __init__(self, allowed: set[tuple[str, str, str]]) -> None:
        self.allowed = allowed

    async def check(self, user: str, relation: str, object_id: str) -> bool:
        return (user, relation, object_id) in self.allowed


class _Upload:
    def __init__(self, document_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        self.id = document_id
        self.owner_id = owner_id


def _grant(document_id: uuid.UUID, member_id: uuid.UUID, relation: str) -> AccessGrant:
    return AccessGrant(
        subject=f"user:{member_id}",
        user_id=member_id,
        relation=relation,
        object_id=f"document:upload-{document_id}",
    )


@pytest.mark.asyncio
async def test_openfga_relation_decides_whether_a_member_can_read() -> None:
    document_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    member_id = uuid.uuid4()
    document = _Upload(document_id, owner_id)
    member = User(
        id=member_id,
        email="member@nexusai.local",
        display_name="Member",
        password_hash="x",
        role="member",
    )
    target = f"document:upload-{document_id}"
    subject = f"user:{member_id}"
    grants = [_grant(document_id, member_id, "analyst")]
    allowed = _Checker({(subject, "analyst", target)})
    denied = _Checker(set())
    assert await allowed_by_openfga(member, document, grants, allowed) is True  # type: ignore[arg-type]
    assert await allowed_by_openfga(member, document, grants, denied) is False  # type: ignore[arg-type]
    assert await allowed_by_openfga(member, document, [], allowed) is False  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_share_writes_the_chosen_relation_and_replaces_the_old_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document_id = uuid.uuid4()
    member_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    written: dict[str, str] = {}
    updated: dict[str, str] = {}
    current = _grant(document_id, member_id, "viewer")

    async def get_document(document: uuid.UUID) -> _Upload:
        assert document == document_id
        return _Upload(document_id, owner_id)

    async def get_by_id(user_id: uuid.UUID) -> User:
        assert user_id == member_id
        return User(
            id=member_id,
            email="member@nexusai.local",
            display_name="Member",
            password_hash="x",
            role="member",
        )

    grants = {"rows": []}

    async def list_grants() -> list[AccessGrant]:
        return list(grants["rows"])

    async def create_permission(
        _client: object,
        _kind: str,
        user_id: uuid.UUID,
        relation: str,
        object_id: str,
    ) -> None:
        written["user"] = str(user_id)
        written["relation"] = relation
        written["object"] = object_id

    async def update_permission(_client: object, grant_id: uuid.UUID, relation: str) -> None:
        assert grant_id == current.id
        updated["relation"] = relation

    monkeypatch.setattr(library, "get_document", get_document)
    monkeypatch.setattr(library, "get_by_id", get_by_id)
    monkeypatch.setattr(library, "list_grants", list_grants)
    monkeypatch.setattr(library, "create_permission", create_permission)
    monkeypatch.setattr(library, "update_permission", update_permission)

    await library.share_document(document_id, member_id, object(), "analyst")  # type: ignore[arg-type]
    assert written == {
        "user": str(member_id),
        "relation": "analyst",
        "object": f"document:upload-{document_id}",
    }

    grants["rows"] = [current]
    await library.share_document(document_id, member_id, object(), "auditor")  # type: ignore[arg-type]
    assert updated["relation"] == "auditor"
