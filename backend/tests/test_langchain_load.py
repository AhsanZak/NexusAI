"""LangChain reads PDFs page by page and splits text that is too long for one chunk."""

import io

import pytest
from pypdf import PdfWriter

from app.documents.extract import EmptyDocument, UnsupportedFile, extract_upload
from app.documents.vectors import chunk_text


def test_a_multipage_pdf_is_read_with_pypdf_and_split() -> None:
    pages = [
        "Warehouse code ZX-44 is on the first page of this long report. " + ("alpha " * 80),
        "The second page keeps going so a large file becomes more than one chunk. "
        + ("beta " * 80),
        "The last page names QM-99 and should survive the split.",
    ]
    extracted = extract_upload("report.pdf", _pdf(pages))

    assert extracted.extractor == "pypdf"
    assert "ZX-44" in extracted.text
    assert "QM-99" in extracted.text
    assert "## Page 1" in extracted.text
    assert "## Page 3" in extracted.text
    chunks = chunk_text(extracted.text, size=200)
    assert len(chunks) > 1
    assert all(len(chunk) <= 200 or "| --- |" in chunk for chunk in chunks)
    assert any("ZX-44" in chunk for chunk in chunks)
    assert any("QM-99" in chunk for chunk in chunks)


def test_an_encrypted_pdf_is_refused_with_a_clear_message() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.encrypt("secret")
    buffer = io.BytesIO()
    writer.write(buffer)

    with pytest.raises(UnsupportedFile, match="encrypted"):
        extract_upload("secret.pdf", buffer.getvalue())


def test_a_corrupt_pdf_is_refused() -> None:
    with pytest.raises(UnsupportedFile, match="could not be read"):
        extract_upload("broken.pdf", b"this is not a pdf")


def test_an_empty_text_file_is_refused() -> None:
    with pytest.raises(EmptyDocument):
        extract_upload("empty.txt", b"   \n")


def test_a_csv_still_becomes_a_table_after_the_loader_reads_it() -> None:
    extracted = extract_upload("rows.csv", b"Region,Revenue\nNorth,42\n")

    assert extracted.extractor == "csvloader"
    assert "| North | 42 |" in extracted.text


def test_a_long_paragraph_is_split_by_the_langchain_splitter() -> None:
    paragraph = " ".join(f"word{index}" for index in range(300))
    chunks = chunk_text(paragraph, size=120)

    assert len(chunks) > 1
    assert all(len(chunk) <= 120 for chunk in chunks)
    assert "word0" in chunks[0]
    assert "word299" in chunks[-1]


def _pdf(pages: list[str]) -> bytes:
    """Build a text PDF that PyPDFLoader can open without another writer library."""
    objects: list[bytes] = []

    def add(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    page_ids: list[int] = []
    for line in pages:
        safe = "".join(char if 32 <= ord(char) < 127 and char not in "()" else " " for char in line)
        stream = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET".encode("latin-1")
        content = f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream"
        content_id = add(content)
        page_id = add(b"PAGE")
        page_ids.append(page_id)
        objects[page_id - 1] = (
            f"<< /Type /Page /Parent PAGES 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_id} 0 R /Resources << /Font << /F1 FONT 0 R >> >> >>"
        ).encode("ascii")
    font_id = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    pages_id = add(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii"))
    catalog_id = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii"))
    for page_id in page_ids:
        objects[page_id - 1] = (
            objects[page_id - 1]
            .replace(b"PAGES", str(pages_id).encode("ascii"))
            .replace(b"FONT", str(font_id).encode("ascii"))
        )
    body = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(body))
        body.extend(f"{number} 0 obj\n".encode("ascii"))
        body.extend(obj)
        body.extend(b"\nendobj\n")
    xref = len(body)
    body.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    body.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        body.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    trailer = (
        f"trailer << /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref}\n%%EOF"
    )
    body.extend(trailer.encode("ascii"))
    return bytes(body)
