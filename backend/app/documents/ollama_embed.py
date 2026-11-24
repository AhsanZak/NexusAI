"""Embed document passages with the Ollama embedding model."""

import httpx

_BATCH = 16


class EmbeddingError(Exception):
    """The Ollama server did not return a vector for every passage."""


async def embed_texts(texts: list[str], *, base_url: str, model: str) -> list[list[float]]:
    """Return one vector per text, in the same order."""
    if not texts:
        return []
    vectors: list[list[float]] = []
    for start in range(0, len(texts), _BATCH):
        batch = texts[start : start + _BATCH]
        vectors.extend(await _embed_batch(batch, base_url=base_url, model=model))
    return vectors


async def _embed_batch(texts: list[str], *, base_url: str, model: str) -> list[list[float]]:
    url = f"{base_url.rstrip('/')}/api/embed"
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, json={"model": model, "input": texts})
    except httpx.HTTPError as exc:
        raise EmbeddingError(f"Ollama embeddings could not reach {base_url}") from exc
    if response.status_code != 200:
        raise EmbeddingError(f"Ollama embeddings returned HTTP {response.status_code}")
    payload = response.json()
    raw = payload.get("embeddings") if isinstance(payload, dict) else None
    if not isinstance(raw, list) or len(raw) != len(texts):
        raise EmbeddingError("Ollama embeddings returned an unexpected response")
    vectors: list[list[float]] = []
    for item in raw:
        if not isinstance(item, list) or not item:
            raise EmbeddingError("Ollama embeddings returned an empty vector")
        vectors.append([float(value) for value in item])
    return vectors
