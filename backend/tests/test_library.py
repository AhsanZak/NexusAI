"""Extraction keeps table cells, and another member cannot read a file without a grant."""

import io
import uuid

from docx import Document
from openpyxl import Workbook

from app.documents.extract import extract_upload, markdown_table
from app.documents.vectors import chunk_text, rank_chunks, term_vector
from app.models.user import User
from app.services.library import can_view


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
