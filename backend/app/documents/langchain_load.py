"""Read uploads with LangChain loaders, one page at a time for large PDFs."""

import os
import tempfile
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

warnings.filterwarnings(
    "ignore",
    message="`langchain-community` is being sunset",
    category=DeprecationWarning,
)
from langchain_community.document_loaders import (  # noqa: E402
    CSVLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document  # noqa: E402


class LoaderFailed(Exception):
    """A LangChain loader stopped before it could return the file text."""


@contextmanager
def temporary_upload(data: bytes, suffix: str) -> Iterator[str]:
    """Give a loader a real path, then delete the file."""
    handle, name = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(handle, data)
        os.close(handle)
        yield name
    finally:
        Path(name).unlink(missing_ok=True)


def load_pdf_pages(path: str) -> tuple[list[str], str | None]:
    """Read each PDF page with PyPDFLoader. A bad later page does not drop earlier ones."""
    loader = PyPDFLoader(path, mode="page", extraction_mode="plain")
    pages, error = _collect(loader.lazy_load())
    if not pages and error:
        raise LoaderFailed(error)
    return [page.page_content or "" for page in pages], error


def load_text(path: str) -> str:
    return _joined(TextLoader(path, encoding="utf-8"))


def load_csv_rows(path: str) -> list[Document]:
    """Let CSVLoader parse the file. Callers turn the rows into a table."""
    pages, error = _collect(CSVLoader(path, encoding="utf-8").lazy_load())
    if error and not pages:
        raise LoaderFailed(error)
    return pages


def load_docx(path: str) -> str:
    return _joined(Docx2txtLoader(path))


def explain_load_error(exc: BaseException) -> str:
    """Turn a loader or parser failure into a short message for the upload form."""
    text = " ".join(str(exc).split())
    lowered = text.lower()
    if "password" in lowered or "decrypt" in lowered or "encrypted" in lowered:
        return "This PDF is encrypted. Remove the password and upload it again."
    if "empty" in lowered and "file" in lowered:
        return "This file is empty."
    if not text:
        text = type(exc).__name__
    if len(text) > 180:
        text = text[:180]
    return f"The file could not be read ({text})."


def _joined(loader: Any) -> str:
    pages, error = _collect(loader.lazy_load())
    if error and not pages:
        raise LoaderFailed(error)
    return "\n\n".join(page.page_content.strip() for page in pages if page.page_content.strip())


def _collect(stream: Iterator[Document]) -> tuple[list[Document], str | None]:
    pages: list[Document] = []
    error: str | None = None
    while True:
        try:
            pages.append(next(stream))
        except StopIteration:
            break
        except Exception as exc:
            error = explain_load_error(exc)
            break
    return pages, error
