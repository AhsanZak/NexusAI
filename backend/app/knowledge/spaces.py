"""The places a person can open to work with one kind of file."""

from dataclasses import dataclass
from pathlib import Path

from app.documents.extract import UnsupportedFile

_IMAGES = (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp", ".gif")


@dataclass(frozen=True)
class KnowledgeSpace:
    id: str
    label: str
    summary: str
    placeholder: str
    extensions: tuple[str, ...]


SPACES: tuple[KnowledgeSpace, ...] = (
    KnowledgeSpace(
        "pdf",
        "PDF",
        "Read a PDF and ask questions about it.",
        "What does this PDF say?",
        (".pdf",),
    ),
    KnowledgeSpace(
        "excel",
        "Excel",
        "Summarize a spreadsheet and ask about its rows.",
        "Summarize this sheet.",
        (".xlsx", ".csv"),
    ),
    KnowledgeSpace(
        "image",
        "Images",
        "Read a picture and ask about the words in it.",
        "What is in this image?",
        _IMAGES,
    ),
    KnowledgeSpace(
        "graph",
        "Graphs",
        "Ask about a chart or graph image.",
        "What does this graph show?",
        _IMAGES,
    ),
    KnowledgeSpace(
        "video",
        "Video",
        "Keep a video in its own chat. Frames are not read yet, so the chat uses the file name.",
        "What can you tell me about this video?",
        (".mp4", ".webm", ".mov"),
    ),
    KnowledgeSpace(
        "document",
        "Other documents",
        "Chat with a text, Markdown, Word, HTML, or JSON file.",
        "What does this document say?",
        (".txt", ".md", ".docx", ".html", ".htm", ".json"),
    ),
)

_BY_ID = {item.id: item for item in SPACES}


class UnknownSpace(Exception):
    """The caller named a space that is not in the catalog."""


class WrongSpaceFile(Exception):
    """The file extension does not belong in the chosen space."""


def space_by_id(space_id: str) -> KnowledgeSpace:
    space = _BY_ID.get(space_id)
    if space is None:
        raise UnknownSpace(space_id)
    return space


def infer_space(filename: str) -> str:
    """Pick a space from the file name when the person did not choose one."""
    suffix = Path(filename).suffix.lower()
    for space in SPACES:
        if space.id == "graph":
            continue
        if suffix in space.extensions:
            return space.id
    raise UnsupportedFile(
        "Upload a PDF, spreadsheet, image, video, text, Word, HTML, or JSON file."
    )


def require_file(space_id: str, filename: str) -> KnowledgeSpace:
    """Reject a file that does not belong in the space the person opened."""
    space = space_by_id(space_id)
    suffix = Path(filename).suffix.lower()
    if suffix not in space.extensions:
        accepted = ", ".join(space.extensions)
        raise WrongSpaceFile(f"The {space.label} space accepts {accepted}.")
    return space
