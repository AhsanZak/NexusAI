"""Pull text and tables out of an uploaded file. The bytes are never executed."""

import csv
import io
from collections.abc import Sequence
from dataclasses import dataclass

from PIL import Image


class UnsupportedFile(Exception):
    """The extension is not one this extractor knows."""


class EmptyDocument(Exception):
    """The file opened, but no text or table cells were found."""


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    extractor: str


_TEXT = {".txt", ".md", ".csv"}
_IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


def extract_upload(filename: str, data: bytes) -> ExtractedDocument:
    """Return the document text. Tables are markdown so the rows stay aligned."""
    suffix = _suffix(filename)
    if suffix in _TEXT:
        extracted = _extract_text(data, suffix)
    elif suffix == ".pdf":
        extracted = _extract_pdf(data)
    elif suffix == ".docx":
        extracted = _extract_docx(data)
    elif suffix == ".xlsx":
        extracted = _extract_xlsx(data)
    elif suffix in _IMAGES:
        extracted = ExtractedDocument(ocr_image(Image.open(io.BytesIO(data))), "rapidocr")
    else:
        raise UnsupportedFile(
            "Upload a text, CSV, PDF, Word (.docx), Excel (.xlsx), or image file"
        )
    if not extracted.text.strip():
        raise EmptyDocument("No text or table cells could be read from this file")
    return extracted


def markdown_table(rows: Sequence[Sequence[object]]) -> str:
    """Render a table as markdown, including an empty body when only a header exists."""
    cleaned = [
        ["" if cell is None else str(cell).replace("\n", " ").strip() for cell in row]
        for row in rows
    ]
    cleaned = [row for row in cleaned if any(cell for cell in row)]
    if not cleaned:
        return ""
    width = max(len(row) for row in cleaned)
    padded = [row + [""] * (width - len(row)) for row in cleaned]
    header = padded[0]
    body = padded[1:] or [[""] * width]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


def ocr_image(image: Image.Image) -> str:
    """Read words from an image. RapidOCR runs locally and does not call a cloud API."""
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR  # type: ignore[import-untyped]

    engine = RapidOCR()
    outcome, _elapsed = engine(np.array(image.convert("RGB")))
    if not outcome:
        return ""
    lines: list[str] = []
    for item in outcome:
        text = item[1] if len(item) > 1 else ""
        if isinstance(text, str) and text.strip():
            lines.append(text.strip())
    return "\n".join(lines)


def _suffix(filename: str) -> str:
    dot = filename.rfind(".")
    if dot < 0:
        return ""
    return filename[dot:].lower()


def _extract_text(data: bytes, suffix: str) -> ExtractedDocument:
    decoded = data.decode("utf-8", errors="replace")
    if suffix != ".csv":
        return ExtractedDocument(decoded, "text")
    rows = list(csv.reader(io.StringIO(decoded)))
    rendered = markdown_table([list(row) for row in rows])
    return ExtractedDocument(rendered or decoded, "csv")


def _extract_pdf(data: bytes) -> ExtractedDocument:
    import pdfplumber

    parts: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            tables = [markdown_table(table) for table in page.extract_tables() or []]
            tables = [table for table in tables if table]
            if tables:
                page_text = f"{page_text}\n\n" + "\n\n".join(tables)
            if len(page_text.strip()) < 40:
                ocr_text = _ocr_pdf_page(data, index - 1)
                if ocr_text:
                    page_text = f"{page_text}\n\n{ocr_text}".strip()
            parts.append(f"## Page {index}\n{page_text}".strip())
    return ExtractedDocument("\n\n".join(parts), "pdfplumber")


def _ocr_pdf_page(data: bytes, page_index: int) -> str:
    import pypdfium2 as pdfium  # type: ignore[import-untyped]

    document = pdfium.PdfDocument(data)
    try:
        page = document[page_index]
        bitmap = page.render(scale=2)
        image = bitmap.to_pil()
    finally:
        document.close()
    return ocr_image(image)


def _extract_docx(data: bytes) -> ExtractedDocument:
    from docx import Document

    document = Document(io.BytesIO(data))
    parts = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        rows = [[cell.text for cell in row.cells] for row in table.rows]
        rendered = markdown_table(rows)
        if rendered:
            parts.append(rendered)
    return ExtractedDocument("\n\n".join(parts), "python-docx")


def _extract_xlsx(data: bytes) -> ExtractedDocument:
    from openpyxl import load_workbook  # type: ignore[import-untyped]

    workbook = load_workbook(io.BytesIO(data), data_only=True, read_only=True)
    parts: list[str] = []
    try:
        for sheet in workbook.worksheets:
            rows = [
                ["" if cell is None else cell for cell in row]
                for row in sheet.iter_rows(values_only=True)
            ]
            rendered = markdown_table(rows)
            if rendered:
                parts.append(f"## {sheet.title}\n{rendered}")
    finally:
        workbook.close()
    return ExtractedDocument("\n\n".join(parts), "openpyxl")
