from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class LogEntry(BaseModel):
    id: str
    timestamp: datetime
    service: str
    level: str
    message: str
    metadata: Dict[str, Any] = {}
    source_ip: Optional[str] = None
    request_id: Optional[str] = None
    region: Optional[str] = None
    response_time: Optional[int] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
