"""Data models for CloudWatch log entries."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, Optional
import json


@dataclass
class CloudWatchLogEntry:
    """Represents a CloudWatch log entry with enriched metadata."""
    
    timestamp: int
    message: str
    log_group: str
    log_stream: str
    
    # AWS Metadata
    region: str
    account_id: str
    service: Optional[str] = None
    
    # Additional fields
    ingestion_time: Optional[int] = None
    event_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_cloudwatch_event(cls, event: Dict[str, Any], 
                              log_group: str, log_stream: str,
                              region: str, account_id: str) -> 'CloudWatchLogEntry':
        """Create from CloudWatch event."""
        return cls(
            timestamp=event['timestamp'],
            message=event['message'],
            log_group=log_group,
            log_stream=log_stream,
            region=region,
            account_id=account_id,
            ingestion_time=event.get('ingestionTime'),
            event_id=event.get('eventId'),
            metadata={}
        )


@dataclass
class LogGroupInfo:
    """Information about a CloudWatch log group."""
    
    log_group_name: str
    region: str
    account_id: str
    creation_time: Optional[int] = None
    stored_bytes: Optional[int] = None
    retention_days: Optional[int] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
