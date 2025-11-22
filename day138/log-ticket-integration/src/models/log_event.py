"""Log event data models"""

from datetime import datetime
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class LogEvent(BaseModel):
    """Log event from distributed logging system"""

    id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    level: str = Field(..., description="Log level (critical, error, warning, info)")
    service: str = Field(..., description="Service name")
    component: Optional[str] = Field(None, description="Component name")
    message: str = Field(..., description="Log message")

    # Context information
    host: Optional[str] = Field(None, description="Host name")
    user_id: Optional[str] = Field(None, description="User ID if applicable")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")

    # Technical details
    stack_trace: Optional[str] = Field(None, description="Stack trace for errors")
    error_code: Optional[str] = Field(None, description="Error code")

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class EventBatch(BaseModel):
    """Batch of log events for processing"""

    events: list[LogEvent]
    batch_id: str
    received_at: datetime = Field(default_factory=datetime.utcnow)
