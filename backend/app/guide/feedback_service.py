"""Feedback service — stores user feedback and query experience data.

Tables required (create in Supabase SQL editor if they don't exist):

CREATE TABLE IF NOT EXISTS user_feedback (
  id BIGSERIAL PRIMARY KEY,
  query TEXT NOT NULL,
  rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  response_snapshot JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS query_logs (
  id BIGSERIAL PRIMARY KEY,
  query TEXT NOT NULL,
  parsed_query JSONB,
  response_summary TEXT,
  confidence TEXT,
  sources_count SMALLINT DEFAULT 0,
  response_time_ms INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

from __future__ import annotations

import logging
from typing import Any

from app.db.supabase import get_supabase

logger = logging.getLogger(__name__)


def submit_feedback(
    query: str,
    rating: int,
    comment: str | None = None,
    response_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Store user feedback for a query response."""
    sb = get_supabase()
    data = {
        "query": query,
        "rating": rating,
        "comment": comment,
        "response_snapshot": response_snapshot,
    }
    try:
        result = sb.table("user_feedback").insert(data).execute()
        if result.data:
            logger.info("Feedback stored: rating=%d for query=%s", rating, query[:50])
            return {"success": True, "id": result.data[0]["id"]}
    except Exception as exc:
        logger.error("Failed to store feedback: %s", exc)
    return {"success": False, "error": "Could not save feedback"}


def log_query(
    query: str,
    parsed_query: dict[str, Any] | None = None,
    response_summary: str | None = None,
    confidence: str | None = None,
    sources_count: int = 0,
    response_time_ms: int = 0,
) -> None:
    """Log a query for analytics."""
    sb = get_supabase()
    data = {
        "query": query,
        "parsed_query": parsed_query,
        "response_summary": response_summary,
        "confidence": confidence,
        "sources_count": sources_count,
        "response_time_ms": response_time_ms,
    }
    try:
        sb.table("query_logs").insert(data).execute()
    except Exception as exc:
        logger.warning("Failed to log query: %s", exc)


def get_recent_feedback(limit: int = 20) -> list[dict[str, Any]]:
    """Retrieve recent feedback entries."""
    sb = get_supabase()
    try:
        result = (
            sb.table("user_feedback")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.warning("Failed to fetch feedback: %s", exc)
        return []


def get_feedback_stats() -> dict[str, Any]:
    """Aggregate feedback statistics."""
    sb = get_supabase()
    try:
        result = sb.table("user_feedback").select("rating").execute()
        ratings = [r["rating"] for r in (result.data or [])]
        if not ratings:
            return {"total": 0, "average_rating": 0, "distribution": {}}
        dist: dict[int, int] = {}
        for r in ratings:
            dist[r] = dist.get(r, 0) + 1
        return {
            "total": len(ratings),
            "average_rating": round(sum(ratings) / len(ratings), 2),
            "distribution": dist,
        }
    except Exception as exc:
        logger.warning("Failed to compute feedback stats: %s", exc)
        return {"total": 0, "average_rating": 0, "distribution": {}}
