from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class SearchRequest(BaseModel):
    query: Optional[str] = ""
    filters: Dict[str, List[str]] = {}
    time_range: Optional[Dict[str, datetime]] = None
    limit: int = 100
    offset: int = 0
    
class SearchResponse(BaseModel):
    logs: List[Dict]
    total_count: int
    facets: List[Dict]
    query_time_ms: float
    applied_filters: Dict[str, List[str]]
