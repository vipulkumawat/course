from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class TimeRange(BaseModel):
    start: datetime
    end: datetime

class AggregationWindow(str, Enum):
    MINUTE = "1m"
    HOUR = "1h"
    DAY = "1d"
    WEEK = "1w"

class MetricType(str, Enum):
    COUNT = "count"
    AVG = "avg"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    P95 = "p95"
    P99 = "p99"

class MetricQuery(BaseModel):
    measurement: str = "http_requests"
    time_range: TimeRange
    aggregation_window: AggregationWindow = AggregationWindow.HOUR
    filters: Dict[str, List[str]] = Field(default_factory=dict)
    metrics: List[MetricType] = Field(default_factory=lambda: [MetricType.COUNT, MetricType.AVG])
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=1000, ge=1, le=10000)

class BIDataResponse(BaseModel):
    schema: Dict[str, str]
    data: List[Dict[str, Any]]
    total_rows: int
    page: int
    page_size: int
    query_time_ms: float
    cached: bool

class MetricSchema(BaseModel):
    name: str
    display_name: str
    data_type: str
    description: str
    unit: Optional[str] = None

class DimensionSchema(BaseModel):
    name: str
    display_name: str
    values: List[str]
    filterable: bool = True

class SchemaResponse(BaseModel):
    metrics: List[MetricSchema]
    dimensions: List[DimensionSchema]
    time_range_available: TimeRange

class ExportRequest(BaseModel):
    date: datetime
    format: str = Field(default="csv", pattern="^(csv|parquet)$")
    metrics: Optional[List[str]] = None
    services: Optional[List[str]] = None

class ExportMetadata(BaseModel):
    export_id: str
    date: datetime
    format: str
    url: str
    row_count: int
    file_size_bytes: int
    columns: List[str]
    generated_at: datetime

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []
    allowed_services: List[str] = []
