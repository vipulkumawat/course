from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class StorageMetric(Base):
    __tablename__ = "storage_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    node_id = Column(String, index=True)
    tenant_id = Column(String, index=True)
    storage_type = Column(String)  # primary, replica, archive
    used_bytes = Column(Float)
    total_bytes = Column(Float)
    extra_metadata = Column(JSON)

class StorageForecast(BaseModel):
    horizon_days: int
    predicted_usage_gb: float
    confidence_interval: tuple[float, float]
    predicted_cost: float
    recommendation: str
    model_accuracy: float
    generated_at: datetime

class CapacityRecommendation(BaseModel):
    current_usage_gb: float
    forecasted_usage_gb: Dict[int, float]  # horizon -> usage
    recommended_capacity_gb: float
    cost_projections: Dict[str, float]
    action_required: bool
    timeline: str
    risk_assessment: str
