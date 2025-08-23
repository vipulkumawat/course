from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel

Base = declarative_base()

class LogEntry(Base):
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    service = Column(String(100), index=True)
    level = Column(String(20), index=True)
    message = Column(Text)
    response_time = Column(Float)
    status_code = Column(Integer)
    endpoint = Column(String(200))
    user_id = Column(String(100))
    
    # Add composite indexes for common queries
    __table_args__ = (
        Index('idx_service_timestamp', 'service', 'timestamp'),
        Index('idx_level_timestamp', 'level', 'timestamp'),
    )

class ChartDataPoint(BaseModel):
    timestamp: datetime
    value: float
    label: str = ""
    metadata: Dict[str, Any] = {}

class TimeSeriesData(BaseModel):
    series_name: str
    data_points: List[ChartDataPoint]
    chart_type: str = "line"
    color: str = "#3b82f6"

class HeatmapData(BaseModel):
    x_labels: List[str]
    y_labels: List[str]
    values: List[List[float]]
    color_scale: str = "viridis"

class DashboardMetrics(BaseModel):
    total_logs: int
    error_rate: float
    avg_response_time: float
    active_services: int
    timestamp: datetime
