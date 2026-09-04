"""Shared feedback and analytics API routes.

POST /api/feedback/submit    — submit rating/feedback for a response
GET  /api/feedback/stats     — get aggregated feedback statistics
POST /api/feedback/checklist — generate a printable PDF checklist
POST /api/feedback/admin/refresh — manually trigger a data refresh scrape
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.guide.feedback_service import submit_feedback, get_feedback_stats
from app.guide.pdf_service import generate_checklist_pdf
from app.guide.scheduler import run_refresh_job

logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    rating: int = Field(..., ge=1, le=5, description="1=unhelpful, 5=very helpful")
    comment: str | None = Field(None, max_length=2000)
    response_snapshot: dict[str, Any] | None = None


class ChecklistRequest(BaseModel):
    """Accepts the full QueryResponse data to generate a PDF."""
    answer: str = ""
    requirements: list[str] = []
    steps: list[str] = []
    fee: str | None = None
    processing_time: str | None = None
    application_method: str | None = None
    application_url: str | None = None
    contact_info: dict[str, Any] | None = None
    eligibility: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/submit")
async def submit_feedback_endpoint(request: FeedbackRequest) -> dict[str, Any]:
    """Submit user feedback for a query response."""
    try:
        result = submit_feedback(
            query=request.query,
            rating=request.rating,
            comment=request.comment,
            response_snapshot=request.response_snapshot,
        )
        return result
    except Exception as exc:
        logger.exception("Feedback submission error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/stats")
async def feedback_stats_endpoint() -> dict[str, Any]:
    """Get aggregated feedback statistics."""
    try:
        return get_feedback_stats()
    except Exception as exc:
        logger.exception("Feedback stats error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/checklist")
async def generate_checklist_endpoint(request: ChecklistRequest) -> Response:
    """Generate a printable PDF checklist for a government service."""
    try:
        data = request.model_dump()
        pdf_bytes = generate_checklist_pdf(data)

        # Detect content type: PDF starts with %PDF-, text fallback starts with anything else
        if pdf_bytes[:5] == b"%PDF-":
            content_type = "application/pdf"
            filename = "pakguide-checklist.pdf"
        else:
            content_type = "text/plain; charset=utf-8"
            filename = "pakguide-checklist.txt"

        return Response(
            content=pdf_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception as exc:
        logger.exception("Checklist generation error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/admin/refresh")
async def manual_refresh_endpoint() -> dict[str, Any]:
    """Manually trigger a data refresh scrape of government websites."""
    try:
        results = run_refresh_job()
        return {"success": True, "results": results}
    except Exception as exc:
        logger.exception("Manual refresh error")
        raise HTTPException(status_code=500, detail=str(exc))
