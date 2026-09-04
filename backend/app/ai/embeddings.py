"""Embedding generation — Google REST API (free) and OpenAI (paid fallback).

Default: Google gemini-embedding-001 with 1536-dim output (free tier).
Matches the existing VECTOR(1536) column in document_chunks.
"""

from __future__ import annotations

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

_GOOGLE_EMBED_URL = "https://generativelanguage.googleapis.com/v1/models/{model}:embedContent"


class EmbeddingQuotaExceededError(RuntimeError):
    """Raised when the embedding provider's free-tier quota is exhausted (429).

    Callers should abort the whole batch — retrying remaining chunks just
    hammers the API and wastes time until the quota resets.
    """


def embed_text(text: str) -> list[float]:
    """Generate a 1536-dim embedding for a single text string."""
    settings = get_settings()

    if settings.embedding_provider == "google":
        return _embed_google(text)
    else:
        return _embed_openai(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    if not texts:
        return []

    settings = get_settings()

    if settings.embedding_provider == "google":
        return _embed_texts_google(texts)
    else:
        return _embed_texts_openai(texts)


# ---------------------------------------------------------------------------
# Google Embeddings (FREE) — via REST API
# ---------------------------------------------------------------------------

def _embed_google(text: str) -> list[float]:
    """Generate embedding using Google REST API (v1).

    Tries each configured API key in order; raises EmbeddingQuotaExceededError
    only when ALL keys are quota-exhausted (429).
    """
    settings = get_settings()
    url = _GOOGLE_EMBED_URL.format(model=settings.embedding_model)

    payload = {
        "model": f"models/{settings.embedding_model}",
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": settings.embedding_dimensions,
    }

    quota_exhausted = False
    for api_key in settings.google_api_keys():
        resp = httpx.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=30,
        )
        if resp.status_code == 429:
            quota_exhausted = True
            continue  # try the next configured key
        if resp.status_code != 200:
            raise RuntimeError(f"Google embedding API error ({resp.status_code}): {resp.text[:300]}")

        data = resp.json()
        return data["embedding"]["values"]

    if quota_exhausted:
        raise EmbeddingQuotaExceededError(
            "Google embedding quota exceeded (all configured keys) — "
            "retry after the daily quota resets"
        )
    raise RuntimeError("Google embedding API: no usable API keys configured")


def _embed_texts_google(texts: list[str]) -> list[list[float]]:
    """Batch embed using Google REST API — one call per text."""
    all_embeddings: list[list[float]] = []
    for text in texts:
        emb = _embed_google(text)
        all_embeddings.append(emb)
    return all_embeddings


# ---------------------------------------------------------------------------
# OpenAI Embeddings (PAID — fallback only)
# ---------------------------------------------------------------------------

_openai_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        settings = get_settings()
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _embed_openai(text: str) -> list[float]:
    settings = get_settings()
    client = _get_openai_client()
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=text,
    )
    return response.data[0].embedding


def _embed_texts_openai(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    client = _get_openai_client()
    all_embeddings: list[list[float]] = []
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=batch,
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)
    return all_embeddings
