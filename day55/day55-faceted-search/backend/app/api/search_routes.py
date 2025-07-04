from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from ..models.search_request import SearchRequest, SearchResponse
from ..services.search_service import SearchService
from ..services.facet_engine import FacetEngine
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])

# Global instances (in production, use dependency injection)
facet_engine = FacetEngine()
search_service = SearchService(facet_engine)

@router.post("/", response_model=SearchResponse)
async def search_logs(search_request: SearchRequest):
    """Perform faceted search on logs"""
    try:
        logger.info(f"Search request: {search_request.dict()}")
        result = await search_service.search(search_request)
        logger.info(f"Search completed in {result.query_time_ms}ms, found {result.total_count} logs")
        return result
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/facets")
async def get_facets(filters: Optional[str] = None):
    """Get available facets with counts"""
    try:
        applied_filters = {}
        if filters:
            # Parse filters from query string (simplified)
            # In production, use proper query parameter parsing
            pass
            
        facets_summary = await facet_engine.get_facets(applied_filters)
        return facets_summary.dict()
    except Exception as e:
        logger.error(f"Facets error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_search_stats():
    """Get search system statistics"""
    facets_summary = await facet_engine.get_facets()
    return {
        "total_logs": facets_summary.total_logs,
        "facet_count": len(facets_summary.facets),
        "system_status": "healthy"
    }
