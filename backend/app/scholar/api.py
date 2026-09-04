"""PakScholar API endpoints for the unified PakMind backend."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/scholar", tags=["scholar"])


class ScholarQuery(BaseModel):
    """Request model for the scholar query endpoint."""
    query: str


@router.post("/query")
async def query_scholar(request: ScholarQuery):
    """POST /api/scholar/query
    
    Two-phase AI-powered eligibility matching:
      1. Check the verified database for eligible opportunities.
      2. If none are eligible, fall back to a web search.
    
    Returns database_matches, web_matches, summaries, and detected language.
    """
    from app.scholar.scholar_service import process_query
    result = await process_query(request.query)
    return result


@router.get("/opportunities")
async def get_opportunities(
    status: str = Query(None, description="Filter by status (e.g. 'example', 'active')"),
    type: str = Query(None, description="Filter by type (e.g. 'scholarship', 'internship')"),
    province: str = Query(None, description="Filter by province"),
    degree_level: str = Query(None, description="Filter by degree level"),
    limit: int = Query(100, ge=1, le=500, description="Max rows to return"),
):
    """GET /api/scholar/opportunities
    
    Returns all opportunities from the database with optional filters.
    """
    from app.db.supabase import get_all_opportunities
    
    opportunities = get_all_opportunities(
        status_filter=status,
        type_filter=type,
        province_filter=province,
        degree_filter=degree_level,
        limit=limit,
    )
    
    return {
        "count": len(opportunities),
        "data": opportunities,
    }
