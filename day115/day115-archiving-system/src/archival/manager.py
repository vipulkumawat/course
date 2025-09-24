import asyncio
import structlog
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import json
import hashlib
from dataclasses import dataclass, asdict

logger = structlog.get_logger()

@dataclass
class LogEntry:
    id: str
    timestamp: datetime
    level: str
    service: str
    message: str
    metadata: Dict
    size_bytes: int
    file_path: str

@dataclass
class ArchivalJob:
    job_id: str
    entries: List[LogEntry]
    status: str = "pending"
    created_at: datetime = None
    compression_ratio: float = 0.0
    storage_tier: str = "cold"
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class ArchivalManager:
    def __init__(self, config):
        self.config = config
        self.jobs = {}
        self.stats = {
            "total_archived": 0,
            "total_compressed_size": 0,
            "total_original_size": 0,
            "compression_ratio": 0.0
        }
        
    async def create_archival_job(self, entries: List[LogEntry]) -> ArchivalJob:
        """Create new archival job for log entries"""
        job_id = hashlib.md5(f"{datetime.now()}{len(entries)}".encode()).hexdigest()[:8]
        
        job = ArchivalJob(
            job_id=job_id,
            entries=entries,
            status="created"
        )
        
        self.jobs[job_id] = job
        logger.info("Created archival job", job_id=job_id, entry_count=len(entries))
        return job
    
    async def process_archival_job(self, job: ArchivalJob) -> bool:
        """Process archival job through complete pipeline"""
        try:
            job.status = "processing"
            
            # Step 1: Validate entries
            await self._validate_entries(job.entries)
            
            # Step 2: Compress data
            compressed_data = await self._compress_entries(job.entries)
            job.compression_ratio = len(compressed_data) / sum(e.size_bytes for e in job.entries)
            
            # Step 3: Store in appropriate tier
            storage_path = await self._store_compressed_data(compressed_data, job)
            
            # Step 4: Extract and index metadata
            await self._extract_metadata(job.entries, storage_path)
            
            # Step 5: Update statistics
            await self._update_stats(job)
            
            job.status = "completed"
            logger.info("Archival job completed", job_id=job.job_id, 
                       compression_ratio=job.compression_ratio)
            return True
            
        except Exception as e:
            job.status = "failed"
            logger.error("Archival job failed", job_id=job.job_id, error=str(e))
            return False
    
    async def _validate_entries(self, entries: List[LogEntry]):
        """Validate log entries before archival"""
        for entry in entries:
            if not entry.id or not entry.timestamp:
                raise ValueError(f"Invalid entry: {entry.id}")
    
    async def _compress_entries(self, entries: List[LogEntry]) -> bytes:
        """Compress log entries based on configuration"""
        import zstandard as zstd
        
        # Serialize entries to JSON with custom datetime handler
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        data = json.dumps([asdict(entry) for entry in entries], default=json_serializer)
        
        # Compress using zstandard
        compressor = zstd.ZstdCompressor(level=self.config.compression.compression_level)
        return compressor.compress(data.encode())
    
    async def _store_compressed_data(self, data: bytes, job: ArchivalJob) -> str:
        """Store compressed data in appropriate storage tier"""
        storage_dir = Path(f"storage/{job.storage_tier}")
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = storage_dir / f"{job.job_id}.zst"
        
        with open(file_path, 'wb') as f:
            f.write(data)
        
        return str(file_path)
    
    async def _extract_metadata(self, entries: List[LogEntry], storage_path: str):
        """Extract searchable metadata from entries"""
        metadata = {
            "entry_count": len(entries),
            "date_range": {
                "start": min(e.timestamp for e in entries).isoformat(),
                "end": max(e.timestamp for e in entries).isoformat()
            },
            "services": list(set(e.service for e in entries)),
            "levels": list(set(e.level for e in entries)),
            "storage_path": storage_path,
            "indexed_at": datetime.now().isoformat()
        }
        
        # Store metadata index
        metadata_dir = Path("metadata")
        metadata_dir.mkdir(exist_ok=True)
        
        with open(metadata_dir / f"{Path(storage_path).stem}_meta.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    
    async def _update_stats(self, job: ArchivalJob):
        """Update archival statistics"""
        original_size = sum(e.size_bytes for e in job.entries)
        compressed_size = original_size * job.compression_ratio
        
        self.stats["total_archived"] += len(job.entries)
        self.stats["total_original_size"] += original_size
        self.stats["total_compressed_size"] += compressed_size
        
        if self.stats["total_original_size"] > 0:
            self.stats["compression_ratio"] = (
                self.stats["total_compressed_size"] / self.stats["total_original_size"]
            )
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of archival job"""
        job = self.jobs.get(job_id)
        return asdict(job) if job else None
    
    def get_statistics(self) -> Dict:
        """Get archival statistics"""
        return self.stats.copy()
