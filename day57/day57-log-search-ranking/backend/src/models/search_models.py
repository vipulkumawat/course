"""
Pydantic models for search API
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class SearchQuery(BaseModel):
    query: str = Field(..., description="Search query text")
    context: Optional[Dict[str, Any]] = Field(None, description="Search context for personalization")
    filters: Optional[Dict[str, str]] = Field(None, description="Additional filters")
    limit: Optional[int] = Field(20, description="Maximum number of results")

class LogResult(BaseModel):
    id: str
    timestamp: str
    level: str
    service: str
    message: str
    metadata: Dict[str, Any]
    relevance_score: float
    final_relevance_score: float
    score_components: Dict[str, float]
    ranking_explanation: str

class SearchResponse(BaseModel):
    query: str
    results: List[LogResult]
    total_hits: int
    ranked_hits: int
    execution_time_ms: float
    suggestions: Optional[List[str]] = None
