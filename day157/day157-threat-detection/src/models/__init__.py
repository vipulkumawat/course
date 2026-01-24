from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ThreatCategory(str, Enum):
    WEB_ATTACK = "web_attack"
    AUTH_ATTACK = "auth_attack"
    SYSTEM_ATTACK = "system_attack"
    FILE_ATTACK = "file_attack"
    DATA_LEAK = "data_leak"

class LogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    source_ip: str
    endpoint: str
    method: str
    payload: str
    user_agent: Optional[str] = None
    user_id: Optional[str] = None
    status_code: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DetectionRule(BaseModel):
    name: str
    pattern: str
    severity: SeverityLevel
    category: ThreatCategory
    action: str
    threshold: Optional[int] = None
    time_window: Optional[int] = None
    distributed: bool = False

class ThreatDetection(BaseModel):
    detection_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    rule_name: str
    severity: SeverityLevel
    category: ThreatCategory
    log_entry: LogEntry
    matched_pattern: str
    confidence: float
    action_taken: str
    context: Dict[str, Any] = Field(default_factory=dict)
