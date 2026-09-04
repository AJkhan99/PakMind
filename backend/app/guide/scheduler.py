"""Data freshness scheduler — periodically re-scrapes government websites.

Uses APScheduler (lightweight, no external cron needed) to run weekly
data ingestion jobs that keep PakGuide's information up-to-date.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Government websites to scrape periodically
SCRAPE_TARGETS = [
    {
        "name": "DG Immigration & Passports",
        "url": "https://www.dgip.gov.pk/",
        "service": "passport",
    },
    {
        "name": "NADRA",
        "url": "https://www.nadra.gov.pk/",
        "service": "cnic",
    },
    {
        "name": "Punjab Excise & Taxation",
        "url": "https://excise.punjab.gov.pk/",
        "service": "driving_licence",
    },
]


def _scrape_and_update(target: dict) -> dict:
    """Scrape a government website and update the database if content changed."""
    import hashlib
    import httpx
    from bs4 import BeautifulSoup
    from app.db.supabase import get_supabase

    sb = get_supabase()
    url = target["url"]
    name = target["name"]

    try:
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("Scrape failed for %s: %s", name, exc)
        return {"target": name, "status": "error", "error": str(exc)}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove scripts/styles
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    content_hash = hashlib.sha256(text.encode()).hexdigest()

    # Check if document exists and content changed
    existing = sb.table("documents").select("*").eq("url", url).execute().data
    if existing and existing[0].get("content_hash") == content_hash:
        logger.info("No changes detected for %s", name)
        return {"target": name, "status": "unchanged"}

    now = datetime.now(timezone.utc).isoformat()
    doc_data = {
        "url": url,
        "title": soup.title.string.strip() if soup.title else name,
        "content": text[:10000],  # Cap at 10k chars
        "content_hash": content_hash,
        "last_verified": now,
        "status": "active",
        "document_type": "web_page",
    }

    if existing:
        doc_id = existing[0]["id"]
        sb.table("documents").update(doc_data).eq("id", doc_id).execute()
        logger.info("Document updated for %s (id=%s)", name, doc_id)
        return {"target": name, "status": "updated", "doc_id": doc_id}
    else:
        # Find or create source
        source = sb.table("sources").select("*").eq("url", url).execute().data
        if source:
            source_id = source[0]["id"]
        else:
            src_data = {
                "name": name,
                "url": url,
                "source_type": "federal_website",
                "trust_level": 5,
                "active": True,
            }
            result = sb.table("sources").insert(src_data).execute()
            source_id = result.data[0]["id"] if result.data else None

        if source_id:
            doc_data["source_id"] = source_id
            result = sb.table("documents").insert(doc_data).execute()
            doc_id = result.data[0]["id"] if result.data else None
            logger.info("New document created for %s (id=%s)", name, doc_id)
            return {"target": name, "status": "created", "doc_id": doc_id}

    return {"target": name, "status": "skipped"}


def run_refresh_job() -> list[dict]:
    """Run the full refresh job — scrape all targets and update DB."""
    logger.info("=== Scheduled refresh job started ===")
    results = []
    for target in SCRAPE_TARGETS:
        result = _scrape_and_update(target)
        results.append(result)
        logger.info("  %s: %s", result["target"], result["status"])
    logger.info("=== Refresh job complete: %d targets processed ===", len(results))
    return results


def setup_scheduler(app=None) -> None:
    """Set up the weekly refresh scheduler.

    Uses a simple asyncio background task approach so we don't need
    additional dependencies. The job runs every 7 days.
    """
    import asyncio

    async def _periodic_refresh():
        """Run refresh every 7 days."""
        while True:
            await asyncio.sleep(7 * 24 * 3600)  # 7 days
            try:
                # Run in executor to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, run_refresh_job)
            except Exception as exc:
                logger.error("Scheduled refresh failed: %s", exc)

    if app is not None:
        @app.on_event("startup")
        async def _start_scheduler():
            asyncio.create_task(_periodic_refresh())
            logger.info("Scheduler started — next refresh in 7 days")

        # Also run once on startup (after a short delay)
        @app.on_event("startup")
        async def _initial_refresh():
            await asyncio.sleep(30)  # Wait 30s after startup
            try:
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(None, run_refresh_job)
                logger.info("Initial refresh complete: %s", results)
            except Exception as exc:
                logger.warning("Initial refresh failed: %s", exc)
