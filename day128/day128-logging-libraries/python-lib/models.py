from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
import json
import uuid

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class LogEntry:
    timestamp: str
    level: LogLevel
    message: str
    service: str
    component: str
    metadata: Dict[str, Any]
    request_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary for JSON serialization"""
        data = asdict(self)
        data['level'] = self.level.value
        return data
    
    def to_json(self) -> str:
        """Convert log entry to JSON string"""
        return json.dumps(self.to_dict())

class LogBatch:
    def __init__(self, max_size: int = 100):
        self.entries = []
        self.max_size = max_size
        self.created_at = datetime.now()
    
    def add_entry(self, entry: LogEntry) -> bool:
        """Add entry to batch. Returns True if batch is full."""
        self.entries.append(entry)
        return len(self.entries) >= self.max_size
    
    def is_empty(self) -> bool:
        return len(self.entries) == 0
    
    def size(self) -> int:
        return len(self.entries)
    
    def to_json(self) -> str:
        """Convert entire batch to JSON"""
        return json.dumps([entry.to_dict() for entry in self.entries])
