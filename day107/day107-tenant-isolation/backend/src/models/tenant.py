"""Tenant data models."""
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TenantTier(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class ResourceQuota(BaseModel):
    """Resource quota configuration."""
    cpu_cores: float = Field(default=1.0, ge=0.1, le=16.0)
    memory_mb: int = Field(default=512, ge=128, le=16384)
    storage_mb: int = Field(default=1024, ge=256, le=102400)
    requests_per_minute: int = Field(default=100, ge=10, le=10000)
    concurrent_connections: int = Field(default=10, ge=1, le=1000)

class ResourceUsage(BaseModel):
    """Current resource usage tracking."""
    tenant_id: str
    cpu_usage_percent: float = 0.0
    memory_usage_mb: int = 0
    storage_usage_mb: int = 0
    active_requests: int = 0
    concurrent_connections: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Tenant(Base):
    """Tenant database model."""
    __tablename__ = "tenants"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    tier = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    quota = Column(JSON, nullable=False)
    
    def get_quota(self) -> ResourceQuota:
        """Get typed quota object."""
        return ResourceQuota(**self.quota)

class TenantMetrics(Base):
    """Tenant metrics storage."""
    __tablename__ = "tenant_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Integer, default=0)
    storage_usage = Column(Integer, default=0)
    request_count = Column(Integer, default=0)
    response_time_ms = Column(Float, default=0.0)
