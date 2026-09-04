"""Vector search wrapper for PakGuide — delegates to shared DB layer."""
from __future__ import annotations
from typing import Any
from app.db.supabase import vector_search_chunks

def search(embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
    return vector_search_chunks(embedding, top_k=top_k)
