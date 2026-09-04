"""Keyword search wrapper for PakWatch — delegates to shared DB layer."""

from __future__ import annotations

from typing import Any

from app.db.supabase import keyword_search_updates, search_updates


def search(query_text: str, limit: int = 5) -> list[dict[str, Any]]:
    return keyword_search_updates(query_text, limit=limit)


def search_by_filters(
    title: str | None = None,
    category: str | None = None,
    province: str | None = None,
    importance: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    return search_updates(
        title=title,
        category=category,
        province=province,
        importance=importance,
        limit=limit,
    )
