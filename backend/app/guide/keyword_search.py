"""Keyword search wrapper for PakGuide — delegates to shared DB layer."""
from __future__ import annotations
from typing import Any
from app.db.supabase import keyword_search_services, search_services

def search(query_text: str, limit: int = 5) -> list[dict[str, Any]]:
    return keyword_search_services(query_text, limit=limit)

def search_by_name(service_name: str, province: str | None = None, city: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    return search_services(service_name=service_name, province=province, city=city, limit=limit)
