from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    start_time: Optional[datetime] = Field(None, description="Start time for search range")
    end_time: Optional[datetime] = Field(None, description="End time for search range")
    log_level: Optional[List[LogLevel]] = Field(None, description="Filter by log levels")
    service_name: Optional[List[str]] = Field(None, description="Filter by service names")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    include_content: bool = Field(True, description="Include full log content")
    sort_by: str = Field("relevance", description="Sort field: relevance, timestamp")
    sort_order: str = Field("desc", description="Sort order: asc, desc")

class LogEntry(BaseModel):
    id: str
    timestamp: datetime
    level: LogLevel
    service_name: str
    message: str
    content: Optional[Dict[str, Any]] = None
    score: Optional[float] = None

class SearchResponse(BaseModel):
    query: str
    total_hits: int
    execution_time_ms: float
    results: List[LogEntry]
    pagination: Dict[str, Any]
    aggregations: Optional[Dict[str, Any]] = None

class SearchMetrics(BaseModel):
    total_queries: int
    avg_response_time_ms: float
    cache_hit_rate: float
    top_queries: List[Dict[str, Any]]
