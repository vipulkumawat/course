from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from typing import List, Optional
from datetime import datetime
from schemas.search import SearchRequest, SearchResponse, LogLevel
from services.search_service import SearchService
from middleware.auth import get_current_user

router = APIRouter()
security = HTTPBearer()
search_service = SearchService()

@router.post("/search", response_model=SearchResponse)
async def search_logs(
    request: SearchRequest,
    current_user = Depends(get_current_user)
):
    """
    Search logs with advanced filtering and ranking capabilities.
    
    - **query**: Full-text search query
    - **start_time**: Filter logs after this timestamp
    - **end_time**: Filter logs before this timestamp
    - **log_level**: Filter by log levels (DEBUG, INFO, WARN, ERROR, FATAL)
    - **service_name**: Filter by service names
    - **limit**: Maximum results (1-1000)
    - **offset**: Pagination offset
    - **sort_by**: Sort field (relevance, timestamp)
    - **sort_order**: Sort order (asc, desc)
    """
    try:
        result = await search_service.search_logs(request, current_user.username)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=SearchResponse)
async def search_logs_get(
    q: str = Query(..., description="Search query"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    log_level: Optional[List[LogLevel]] = Query(None, description="Log levels"),
    service_name: Optional[List[str]] = Query(None, description="Service names"),
    limit: int = Query(100, ge=1, le=1000, description="Limit"),
    offset: int = Query(0, ge=0, description="Offset"),
    sort_by: str = Query("relevance", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    current_user = Depends(get_current_user)
):
    """GET endpoint for search with query parameters"""
    request = SearchRequest(
        query=q,
        start_time=start_time,
        end_time=end_time,
        log_level=log_level,
        service_name=service_name,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await search_logs(request, current_user)

@router.get("/suggest")
async def suggest_queries(
    q: str = Query(..., description="Partial query"),
    current_user = Depends(get_current_user)
):
    """Get query suggestions based on popular searches"""
    # Implementation for query suggestions
    suggestions = [
        f"{q} error",
        f"{q} warning",
        f"{q} timeout",
        f"{q} failed"
    ]
    return {"suggestions": suggestions[:5]}

@router.get("/metrics")
async def get_search_metrics(current_user = Depends(get_current_user)):
    """Get search metrics for the current user"""
    # Implementation for user-specific metrics
    return {
        "total_queries": 142,
        "avg_response_time_ms": 89.5,
        "cache_hit_rate": 0.73,
        "top_queries": [
            {"query": "error payment", "count": 23},
            {"query": "timeout database", "count": 18}
        ]
    }
