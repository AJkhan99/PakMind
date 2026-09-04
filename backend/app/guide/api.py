"""PakGuide API routes.

POST /api/guide/search  — return matching services (no AI generation)
POST /api/guide/query   — full RAG pipeline with verified AI answer
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.guide.guide_service import search_services, query_answer

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Natural-language search query")


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Natural-language question about a government service")


class SourceResponse(BaseModel):
    title: str | None = None
    url: str | None = None
    source_name: str | None = None
    last_verified: str | None = None


class QueryResponse(BaseModel):
    module: str = "guide"
    answer: str
    requirements: list[str] = []
    steps: list[str] = []
    fee: str | None = None
    processing_time: str | None = None
    application_method: str | None = None
    application_url: str | None = None
    contact_info: dict[str, Any] | None = None
    eligibility: str | None = None
    sources: list[SourceResponse] = []
    last_verified: str | None = None
    confidence: str = "medium"
    warnings: list[str] = []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/search")
async def search_endpoint(request: SearchRequest) -> dict[str, Any]:
    """Return relevant government services without generating an AI answer."""
    try:
        result = search_services(request.query)
        return result
    except Exception as exc:
        logger.exception("Search endpoint error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest) -> QueryResponse:
    """Full RAG pipeline — answer a natural-language question with verified information."""
    try:
        result = query_answer(request.query)
        return QueryResponse(**result)
    except Exception as exc:
        logger.exception("Query endpoint error")
        raise HTTPException(status_code=500, detail=str(exc))
