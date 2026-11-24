"""Chunk extracted text and rank those chunks by a local term vector."""

import math
import re
import zlib

from langchain_text_splitters import RecursiveCharacterTextSplitter

_TOKEN = re.compile(r"[a-z0-9]+")
_DIMENSIONS = 256


def chunk_text(text: str, size: int = 900, table_limit: int = 4000) -> list[str]:
    """Split prose with LangChain and keep a markdown table together with its header."""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        compact = text.strip()
        return [compact] if compact else []
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if _is_table_block(paragraph):
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_table_chunks(paragraph, table_limit))
            continue
        if len(paragraph) > size:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_with_langchain(paragraph, size))
            continue
        if current and len(current) + len(paragraph) + 2 > size:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks


def _split_with_langchain(paragraph: str, size: int) -> list[str]:
    """Break one long passage. Overlap keeps a large PDF from cutting a sentence in half."""
    overlap = min(120, max(size // 5, 0))
    if overlap >= size:
        overlap = 0
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    return [piece.strip() for piece in splitter.split_text(paragraph) if piece.strip()]


def _is_table_block(text: str) -> bool:
    return "| --- |" in text or "|---|" in text.replace(" ", "")


def _table_chunks(block: str, limit: int) -> list[str]:
    if len(block) <= limit:
        return [block]
    lines = block.splitlines()
    separator = next(
        (index for index, line in enumerate(lines) if "---" in line and "|" in line),
        None,
    )
    if separator is None:
        return [block[index : index + limit] for index in range(0, len(block), limit)]
    preamble = lines[: separator + 1]
    body = lines[separator + 1 :]
    chunks: list[str] = []
    current = list(preamble)
    for row in body:
        candidate = [*current, row]
        if len("\n".join(candidate)) > limit and len(current) > len(preamble):
            chunks.append("\n".join(current))
            current = [*preamble, row]
        else:
            current = candidate
    if len(current) > len(preamble):
        chunks.append("\n".join(current))
    return chunks or [block]


def term_vector(text: str) -> list[float]:
    """Map tokens into a fixed vector. The same words land in the same positions."""
    counts = [0.0] * _DIMENSIONS
    for token in _TOKEN.findall(text.lower()):
        counts[zlib.crc32(token.encode()) % _DIMENSIONS] += 1.0
    norm = math.sqrt(sum(value * value for value in counts)) or 1.0
    return [value / norm for value in counts]


def cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    return sum(one * other for one, other in zip(left, right, strict=True))


def rank_by_vector(
    query_vector: list[float],
    chunks: list[tuple[int, str, list[float]]],
    limit: int = 4,
) -> list[int]:
    """Return chunk indexes closest to a query vector, highest score first."""
    scored = sorted(
        ((cosine(query_vector, vector), index) for index, _content, vector in chunks),
        reverse=True,
    )
    positive = [index for score, index in scored[:limit] if score > 0]
    if positive:
        return positive
    return [scored[0][1]] if scored else []


def rank_chunks(
    query: str,
    chunks: list[tuple[int, str, list[float]]],
    limit: int = 4,
) -> list[int]:
    """Return chunk indexes closest to the question, highest score first."""
    return rank_by_vector(term_vector(query), chunks, limit)
