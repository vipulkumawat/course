"""
Data models for the tiered storage system.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel


class LogEntry(BaseModel):
    """Represents a log entry in the storage system."""
    
    entry_id: str
    message: str
    level: str
    service: str
    priority: str = "normal"
    metadata: Dict[str, Any] = {}
    timestamp: datetime
    stored_at: datetime
    tier: str
    size_bytes: int = 0
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageTier(str, Enum):
    """Storage tier types."""
    
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    ARCHIVE = "archive"


class TierMetadata(BaseModel):
    """Metadata for a storage tier."""
    
    tier: StorageTier
    path: str
    max_size_gb: int
    cost_per_gb_month: float
    access_latency_ms: int
    durability_level: str
    created_at: datetime
    last_accessed: Optional[datetime] = None
    total_entries: int = 0
    total_size_bytes: int = 0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MigrationRecord(BaseModel):
    """Record of a data migration operation."""
    
    migration_id: str
    from_tier: StorageTier
    to_tier: StorageTier
    entry_ids: list[str]
    migrated_at: datetime
    size_bytes: int
    cost_savings: float
    status: str  # "pending", "in_progress", "completed", "failed"
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
