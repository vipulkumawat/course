from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json

class IOCType(Enum):
    """Types of indicators of compromise"""
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    FILE_HASH = "file_hash"
    URL = "url"
    EMAIL = "email"
    USER_AGENT = "user_agent"

class Severity(Enum):
    """Threat severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class IOCIndicator:
    """Indicator of compromise data structure"""
    value: str
    ioc_type: IOCType
    severity: Severity
    source: str
    description: str = ""
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "type": self.ioc_type.value,
            "severity": self.severity.value,
            "source": self.source,
            "description": self.description,
            "confidence": self.confidence,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "metadata": self.metadata
        }

@dataclass
class SecurityAlert:
    """Security alert generated from IOC match"""
    alert_id: str
    timestamp: datetime
    matched_ioc: IOCIndicator
    log_entry: Dict[str, Any]
    severity: Severity
    confidence_score: float
    additional_context: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    
    def to_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp.isoformat(),
            "matched_ioc": self.matched_ioc.to_dict(),
            "log_entry": self.log_entry,
            "severity": self.severity.value,
            "confidence_score": self.confidence_score,
            "additional_context": self.additional_context,
            "acknowledged": self.acknowledged
        }
