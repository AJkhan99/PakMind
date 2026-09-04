"""Supabase database client and query helpers for PakMind unified backend.

IMPORTANT: This module connects to the *existing* PakMind Supabase database.
It does NOT create any tables. It only performs SELECT / INSERT / UPSERT
against the already-provisioned schema.

Covers: sources, documents, document_chunks (shared),
        government_services (PakGuide), government_updates (PakWatch),
        topic_digests (PakWatch), web_answers (PakWatch),
        opportunities (PakScholar).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from supabase import Client, create_client

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_supabase() -> Client:
    """Return a singleton Supabase client (anon key)."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


# ---------------------------------------------------------------------------
# Sources helpers
# ---------------------------------------------------------------------------

def get_all_sources(active_only: bool = True) -> list[dict[str, Any]]:
    sb = get_supabase()
    query = sb.table("sources").select("*")
    if active_only:
        query = query.eq("active", True)
    return query.execute().data or []


def upsert_source(data: dict[str, Any]) -> dict[str, Any] | None:
    sb = get_supabase()
    url = data.get("url")
    if url:
        existing = sb.table("sources").select("*").eq("url", url).execute().data
        if existing:
            result = sb.table("sources").update(data).eq("url", url).execute()
            return result.data[0] if result.data else None
    result = sb.table("sources").insert(data).execute()
    return result.data[0] if result.data else None


def get_source_by_url(url: str) -> dict[str, Any] | None:
    sb = get_supabase()
    result = sb.table("sources").select("*").eq("url", url).execute()
    return result.data[0] if result.data else None


def get_source_by_id(source_id: str) -> dict[str, Any] | None:
    sb = get_supabase()
    result = sb.table("sources").select("*").eq("id", source_id).execute()
    return result.data[0] if result.data else None


def update_source_last_checked(source_id: str) -> None:
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    sb.table("sources").update({"last_checked": now}).eq("id", source_id).execute()


# ---------------------------------------------------------------------------
# Documents helpers
# ---------------------------------------------------------------------------

def get_document_by_url(url: str) -> dict[str, Any] | None:
    sb = get_supabase()
    result = sb.table("documents").select("*").eq("url", url).execute()
    return result.data[0] if result.data else None


def get_document_by_id(doc_id: str) -> dict[str, Any] | None:
    sb = get_supabase()
    result = sb.table("documents").select("*").eq("id", doc_id).execute()
    return result.data[0] if result.data else None


def upsert_document(data: dict[str, Any]) -> dict[str, Any] | None:
    sb = get_supabase()
    url = data.get("url")
    if url:
        existing = sb.table("documents").select("*").eq("url", url).execute().data
        if existing:
            result = sb.table("documents").update(data).eq("url", url).execute()
            return result.data[0] if result.data else None
    result = sb.table("documents").insert(data).execute()
    return result.data[0] if result.data else None


def update_document(doc_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    sb = get_supabase()
    result = sb.table("documents").update(updates).eq("id", doc_id).execute()
    return result.data[0] if result.data else None


# ---------------------------------------------------------------------------
# Document chunks helpers
# ---------------------------------------------------------------------------

def get_chunks_by_document(doc_id: str) -> list[dict[str, Any]]:
    sb = get_supabase()
    return sb.table("document_chunks").select("*").eq("document_id", doc_id).execute().data or []


def delete_chunks_by_document(doc_id: str) -> None:
    sb = get_supabase()
    sb.table("document_chunks").delete().eq("document_id", doc_id).execute()


def insert_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not chunks:
        return []
    sb = get_supabase()
    result = sb.table("document_chunks").insert(chunks).execute()
    return result.data or []


def get_chunks_missing_embeddings(limit: int = 100) -> list[dict[str, Any]]:
    sb = get_supabase()
    result = (
        sb.table("document_chunks")
        .select("id, content")
        .filter("embedding", "is", "null")
        .limit(limit)
        .execute()
    )
    return result.data or []


def update_chunk_embedding(chunk_id: str, embedding: list[float]) -> None:
    sb = get_supabase()
    sb.table("document_chunks").update({"embedding": embedding}).eq("id", chunk_id).execute()


def vector_search_chunks(
    embedding: list[float],
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Perform cosine-similarity vector search on document_chunks."""
    sb = get_supabase()
    try:
        rpc_params: dict[str, Any] = {
            "query_embedding": embedding,
            "match_count": top_k,
        }
        if filters:
            rpc_params["filter_metadata"] = filters
        result = sb.rpc("match_document_chunks", rpc_params).execute()
        return result.data or []
    except Exception:
        logger.warning("RPC match_document_chunks not available, falling back to client-side search")
        return _client_side_vector_search(sb, embedding, top_k, filters)


def _client_side_vector_search(
    sb: Client,
    embedding: list[float],
    top_k: int,
    filters: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Fallback: fetch chunks and compute cosine similarity client-side."""
    import json
    import numpy as np

    query = sb.table("document_chunks").select("id, document_id, content, metadata, embedding")
    result = query.execute()
    chunks = result.data or []

    if not chunks:
        return []

    query_vec = np.array(embedding, dtype=np.float64)
    scored = []
    for chunk in chunks:
        if not chunk.get("embedding"):
            continue
        if filters and chunk.get("metadata"):
            meta = chunk["metadata"]
            if any(meta.get(k) != v for k, v in filters.items()):
                continue
        raw = chunk["embedding"]
        if isinstance(raw, str):
            try:
                emb_array = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                try:
                    stripped = raw.strip("[]")
                    emb_array = [float(x.strip()) for x in stripped.split(",") if x.strip()]
                except (ValueError, TypeError):
                    continue
        elif isinstance(raw, list):
            emb_array = raw
        else:
            continue
        try:
            emb = np.array(emb_array, dtype=np.float64)
        except (ValueError, TypeError):
            continue
        cos_sim = float(np.dot(query_vec, emb) / (np.linalg.norm(query_vec) * np.linalg.norm(emb) + 1e-10))
        chunk["similarity"] = cos_sim
        scored.append(chunk)

    scored.sort(key=lambda c: c["similarity"], reverse=True)
    return scored[:top_k]


# ---------------------------------------------------------------------------
# Government Services helpers (PakGuide)
# ---------------------------------------------------------------------------

def search_services(
    service_name: str | None = None,
    province: str | None = None,
    city: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search government_services with optional filters."""
    sb = get_supabase()
    select_fields = "*, documents(url, title, last_verified, sources(name, url, trust_level))"
    try:
        query = sb.table("government_services").select(select_fields)
        if service_name:
            query = query.ilike("name", f"%{service_name}%")
        if province:
            query = query.ilike("province", f"%{province}%")
        if city:
            query = query.ilike("city", f"%{city}%")
        query = query.eq("status", "active").limit(limit)
        result = query.execute()
        if result.data:
            return result.data
    except Exception as exc:
        logger.warning("search_services nested join failed: %s — falling back", exc)

    try:
        query = sb.table("government_services").select("*")
        if service_name:
            query = query.ilike("name", f"%{service_name}%")
        if province:
            query = query.ilike("province", f"%{province}%")
        if city:
            query = query.ilike("city", f"%{city}%")
        query = query.eq("status", "active").limit(limit)
        return query.execute().data or []
    except Exception as exc:
        logger.error("search_services fallback also failed: %s", exc)
        return []


def get_service_by_id(service_id: str) -> dict[str, Any] | None:
    sb = get_supabase()
    try:
        result = sb.table("government_services").select(
            "*, documents(url, title, last_verified, sources(name, url, trust_level))"
        ).eq("id", service_id).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    result = sb.table("government_services").select("*").eq("id", service_id).execute()
    return result.data[0] if result.data else None


def upsert_service(data: dict[str, Any]) -> dict[str, Any] | None:
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    data.setdefault("created_at", now)
    data["updated_at"] = now
    name = data.get("name")
    province = data.get("province")
    city = data.get("city")
    if name and province and city:
        existing = (
            sb.table("government_services")
            .select("*").eq("name", name).eq("province", province).eq("city", city)
            .execute().data
        )
        if existing:
            result = (
                sb.table("government_services")
                .update(data).eq("name", name).eq("province", province).eq("city", city)
                .execute()
            )
            return result.data[0] if result.data else None
    result = sb.table("government_services").insert(data).execute()
    return result.data[0] if result.data else None


def keyword_search_services(query_text: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search government_services by name and description using ILIKE."""
    sb = get_supabase()
    try:
        results = (
            sb.table("government_services")
            .select("*, documents(url, title, last_verified, sources(name, url, trust_level))")
            .or_(f"name.ilike.%{query_text}%,description.ilike.%{query_text}%")
            .eq("status", "active")
            .limit(limit)
            .execute()
        )
        if results.data:
            return results.data
    except Exception as exc:
        logger.warning("Nested join query failed: %s — falling back", exc)

    try:
        results = (
            sb.table("government_services")
            .select("*")
            .or_(f"name.ilike.%{query_text}%,description.ilike.%{query_text}%")
            .eq("status", "active")
            .limit(limit)
            .execute()
        )
        return results.data or []
    except Exception as exc:
        logger.error("Simple keyword search also failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Government Updates helpers (PakWatch)
# ---------------------------------------------------------------------------

def search_updates(
    title: str | None = None,
    category: str | None = None,
    province: str | None = None,
    department: str | None = None,
    organization: str | None = None,
    importance: str | None = None,
    status: str = "active",
    limit: int = 20,
) -> list[dict[str, Any]]:
    sb = get_supabase()
    select_fields = "*, documents(url, title, last_verified, sources(name, url, trust_level))"
    try:
        query = sb.table("government_updates").select(select_fields)
        if title:
            query = query.ilike("title", f"%{title}%")
        if category:
            query = query.eq("category", category)
        if province:
            query = query.ilike("province", f"%{province}%")
        if department:
            query = query.ilike("department", f"%{department}%")
        if organization:
            query = query.ilike("organization", f"%{organization}%")
        if importance:
            query = query.eq("importance", importance)
        if status:
            query = query.eq("status", status)
        query = query.order("published_date", desc=True).limit(limit)
        result = query.execute()
        if result.data:
            return result.data
    except Exception as exc:
        logger.warning("search_updates nested join failed: %s — falling back", exc)

    try:
        query = sb.table("government_updates").select("*")
        if title:
            query = query.ilike("title", f"%{title}%")
        if category:
            query = query.eq("category", category)
        if province:
            query = query.ilike("province", f"%{province}%")
        if department:
            query = query.ilike("department", f"%{department}%")
        if organization:
            query = query.ilike("organization", f"%{organization}%")
        if importance:
            query = query.eq("importance", importance)
        if status:
            query = query.eq("status", status)
        query = query.order("published_date", desc=True).limit(limit)
        return query.execute().data or []
    except Exception as exc:
        logger.error("search_updates fallback also failed: %s", exc)
        return []


def get_update_by_id(update_id: str) -> dict[str, Any] | None:
    sb = get_supabase()
    try:
        result = sb.table("government_updates").select(
            "*, documents(url, title, last_verified, sources(name, url, trust_level))"
        ).eq("id", update_id).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    result = sb.table("government_updates").select("*").eq("id", update_id).execute()
    return result.data[0] if result.data else None


def get_latest_updates(limit: int = 20, category: str | None = None, province: str | None = None) -> list[dict[str, Any]]:
    return search_updates(category=category, province=province, limit=limit)


def upsert_update(data: dict[str, Any]) -> dict[str, Any] | None:
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    data.setdefault("created_at", now)
    data["updated_at"] = now
    title = data.get("title")
    category = data.get("category")
    province = data.get("province")
    if title and category:
        query = sb.table("government_updates").select("*").eq("title", title).eq("category", category)
        if province:
            query = query.eq("province", province)
        existing = query.execute().data
        if existing:
            result = sb.table("government_updates").update(data).eq("id", existing[0]["id"]).execute()
            return result.data[0] if result.data else None
    result = sb.table("government_updates").insert(data).execute()
    return result.data[0] if result.data else None


def keyword_search_updates(query_text: str, limit: int = 10) -> list[dict[str, Any]]:
    sb = get_supabase()
    keywords = [w.strip(",.?!:;()") for w in query_text.lower().split()]
    keywords = [w for w in keywords if len(w) > 2][:6]
    if not keywords:
        keywords = [query_text.strip()]
    or_parts = []
    for kw in keywords:
        for field in ("title", "summary", "department", "organization"):
            or_parts.append(f"{field}.ilike.%{kw}%")
    or_clause = ",".join(or_parts)
    try:
        results = (
            sb.table("government_updates")
            .select("*, documents(url, title, last_verified, sources(name, url, trust_level))")
            .or_(or_clause).eq("status", "active")
            .order("published_date", desc=True).limit(limit)
            .execute()
        )
        if results.data:
            return results.data
    except Exception as exc:
        logger.warning("Nested join keyword search failed: %s — falling back", exc)
    try:
        results = (
            sb.table("government_updates").select("*")
            .or_(or_clause).eq("status", "active")
            .order("published_date", desc=True).limit(limit)
            .execute()
        )
        return results.data or []
    except Exception as exc:
        logger.error("Keyword search fallback also failed: %s", exc)
        return []


def get_update_categories() -> list[dict[str, Any]]:
    sb = get_supabase()
    try:
        result = sb.rpc("get_update_categories").execute()
        if result.data:
            return result.data
    except Exception:
        pass
    all_updates = sb.table("government_updates").select("category").eq("status", "active").execute().data or []
    counts: dict[str, int] = {}
    for u in all_updates:
        cat = u.get("category", "other")
        counts[cat] = counts.get(cat, 0) + 1
    return [{"category": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]


# ---------------------------------------------------------------------------
# Topic digests helpers (PakWatch)
# ---------------------------------------------------------------------------

def upsert_topic_digest(data: dict[str, Any]) -> dict[str, Any] | None:
    sb = get_supabase()
    result = sb.table("topic_digests").upsert(data, on_conflict="topic").execute()
    return (result.data or [None])[0]


def get_topic_digests() -> list[dict[str, Any]]:
    sb = get_supabase()
    return (
        sb.table("topic_digests")
        .select("*").order("generated_at", desc=True)
        .execute().data or []
    )


# ---------------------------------------------------------------------------
# Web answers cache helpers (PakWatch)
# ---------------------------------------------------------------------------

def insert_web_answer(data: dict[str, Any]) -> dict[str, Any] | None:
    sb = get_supabase()
    result = sb.table("web_answers").insert(data).execute()
    return (result.data or [None])[0]


def get_recent_web_answers(ttl_hours: int) -> list[dict[str, Any]]:
    sb = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=ttl_hours)).isoformat()
    return (
        sb.table("web_answers")
        .select("id, question, question_embedding, answer, what_changed, "
                "who_affected, effective_date, sources, created_at")
        .filter("created_at", "gte", cutoff)
        .limit(200)
        .execute().data or []
    )


# ---------------------------------------------------------------------------
# Opportunities helpers (PakScholar)
# ---------------------------------------------------------------------------

def get_all_opportunities(
    status_filter: str | None = None,
    type_filter: str | None = None,
    province_filter: str | None = None,
    degree_filter: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """Fetch opportunities with optional filters, ordered by deadline."""
    sb = get_supabase()
    query = sb.table("opportunities").select("*")
    if status_filter:
        query = query.eq("status", status_filter)
    if type_filter:
        query = query.eq("type", type_filter)
    if province_filter:
        query = query.ilike("province", f"%{province_filter}%")
    if degree_filter:
        query = query.ilike("degree_level", f"%{degree_filter}%")
    query = query.order("deadline", desc=False).limit(limit)
    return query.execute().data or []


def get_opportunities_by_titles(titles: list[str]) -> dict[str, dict[str, Any]]:
    """Bulk-fetch opportunities by title, returning {title: row}."""
    if not titles:
        return {}
    sb = get_supabase()
    result = sb.table("opportunities").select("*").in_("title", titles).execute()
    rows = result.data or []
    return {r["title"]: r for r in rows if r.get("title")}
