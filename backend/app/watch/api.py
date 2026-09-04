"""PakWatch API routes.

POST /api/watch/search          — return matching updates (no AI generation)
POST /api/watch/query           — full RAG pipeline with verified AI answer
GET  /api/watch/latest           — return newest updates with optional filters
GET  /api/watch/categories       — return available categories and counts
GET  /api/watch/topics           — return pre-computed hot-topic digests
POST /api/watch/topics/refresh   — regenerate all hot-topic digests
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.watch.watch_service import (
    search_updates_api,
    query_answer,
    latest_updates,
    categories_endpoint,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Natural-language search query")


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Natural-language question about government updates")


class SourceResponse(BaseModel):
    title: str | None = None
    url: str | None = None
    source_name: str | None = None
    published_date: str | None = None
    last_verified: str | None = None


class UpdateSummary(BaseModel):
    title: str | None = None
    category: str | None = None
    department: str | None = None
    province: str | None = None
    summary: str | None = None
    importance: str | None = None
    published_date: str | None = None
    what_changed: str | None = None


class QueryResponse(BaseModel):
    module: str = "watch"
    answer: str
    updates: list[dict[str, Any]] = []
    sources: list[SourceResponse] = []
    what_changed: str | None = None
    who_affected: str | None = None
    effective_date: str | None = None
    last_verified: str | None = None
    confidence: str = "medium"
    warnings: list[str] = []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/search")
async def search_endpoint(request: SearchRequest) -> dict[str, Any]:
    """Return relevant government updates without generating an AI answer."""
    try:
        return search_updates_api(request.query)
    except Exception as exc:
        logger.exception("Search endpoint error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest) -> QueryResponse:
    """Full RAG pipeline — answer a natural-language question with verified government information."""
    try:
        result = query_answer(request.query)
        return QueryResponse(**result)
    except Exception as exc:
        logger.exception("Query endpoint error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/latest")
async def latest_endpoint(
    category: str | None = Query(None, description="Filter by category"),
    province: str | None = Query(None, description="Filter by province"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
) -> dict[str, Any]:
    """Return the newest government updates."""
    try:
        return latest_updates(limit=limit, category=category, province=province)
    except Exception as exc:
        logger.exception("Latest endpoint error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/categories")
async def categories_route() -> dict[str, Any]:
    """Return available update categories with counts."""
    try:
        return categories_endpoint()
    except Exception as exc:
        logger.exception("Categories endpoint error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/topics")
async def topics_route() -> dict[str, Any]:
    """Return pre-computed hot-topic digests."""
    from app.watch.digest_service import topic_digests_endpoint

    try:
        return topic_digests_endpoint()
    except Exception as exc:
        logger.exception("Topics endpoint error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/topics/refresh")
async def refresh_topics_route() -> dict[str, Any]:
    """Regenerate all topic digests (runs in threadpool; ~30-60s for 6 topics)."""
    from app.watch.digest_service import generate_topic_digests

    try:
        digests = generate_topic_digests()
        return {"module": "watch", "refreshed": len(digests), "topics": digests}
    except Exception as exc:
        logger.exception("Topics refresh error")
        raise HTTPException(status_code=500, detail=str(exc))
