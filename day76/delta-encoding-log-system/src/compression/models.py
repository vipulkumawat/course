from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import hashlib

@dataclass
class LogEntry:
    timestamp: str
    level: str
    service: str
    message: str
    metadata: Dict[str, Any]
    entry_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.entry_id:
            self.entry_id = self._generate_id()
    
    def _generate_id(self) -> str:
        content = f"{self.timestamp}{self.service}{self.message}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        return cls(**data)

@dataclass
class DeltaEntry:
    entry_id: str
    baseline_id: str
    field_deltas: Dict[str, Any]
    compression_ratio: float
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

@dataclass
class CompressionChunk:
    chunk_id: str
    baseline_entry: LogEntry
    delta_entries: List[DeltaEntry]
    total_entries: int
    compressed_size: int
    original_size: int
    compression_ratio: float
    created_at: datetime
    
    def get_storage_efficiency(self) -> float:
        return (1 - self.compressed_size / self.original_size) * 100
