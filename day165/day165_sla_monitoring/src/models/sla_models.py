from pydantic import BaseModel
from typing import Dict, List, Literal
from datetime import datetime
from enum import Enum

class ServiceTier(str, Enum):
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"

class MetricType(str, Enum):
    LATENCY = "latency"
    AVAILABILITY = "availability"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"

class SLIMetric(BaseModel):
    metric_type: MetricType
    value: float
    timestamp: datetime
    service_tier: ServiceTier

class SLOViolation(BaseModel):
    slo_name: str
    service_tier: ServiceTier
    actual_value: float
    target_value: float
    breach_duration_seconds: int
    severity: Literal["critical", "warning", "info"]
    timestamp: datetime
