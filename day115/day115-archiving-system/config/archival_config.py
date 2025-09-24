from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import timedelta

class CompressionConfig(BaseModel):
    algorithms: Dict[str, str] = {
        "json": "zstd",
        "text": "lz4", 
        "binary": "zstd"
    }
    compression_level: int = 3
    chunk_size: int = 1024 * 1024  # 1MB

class StorageTierConfig(BaseModel):
    hot_retention_days: int = 30
    warm_retention_days: int = 90
    cold_retention_days: int = 365
    deep_storage_years: int = 7

class ArchivalConfig(BaseModel):
    batch_size: int = 10000
    max_workers: int = 4
    compression: CompressionConfig = CompressionConfig()
    storage_tiers: StorageTierConfig = StorageTierConfig()
    metadata_extraction: bool = True
    verify_integrity: bool = True
    schedule_interval_hours: int = 6

config = ArchivalConfig()
