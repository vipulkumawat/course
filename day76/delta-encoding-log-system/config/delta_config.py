from dataclasses import dataclass
from typing import Dict, Any
import os

@dataclass
class DeltaEncodingConfig:
    # Compression settings
    baseline_frequency: int = 100  # Create baseline every N entries
    max_delta_chain: int = 50     # Max deltas before forcing baseline
    compression_threshold: float = 0.3  # Min compression ratio to maintain
    
    # Storage settings
    chunk_size: int = 1000        # Entries per storage chunk
    storage_path: str = "data/compressed_logs"
    backup_path: str = "data/backups"
    
    # Performance settings
    reconstruction_cache_size: int = 1000
    batch_size: int = 100
    max_workers: int = 4
    
    # Dashboard settings
    dashboard_port: int = 8080
    update_interval: int = 5      # Seconds
    
    @classmethod
    def from_env(cls) -> 'DeltaEncodingConfig':
        return cls(
            baseline_frequency=int(os.getenv('BASELINE_FREQ', 100)),
            max_delta_chain=int(os.getenv('MAX_DELTA_CHAIN', 50)),
            compression_threshold=float(os.getenv('COMPRESSION_THRESHOLD', 0.3)),
            chunk_size=int(os.getenv('CHUNK_SIZE', 1000)),
            storage_path=os.getenv('STORAGE_PATH', 'data/compressed_logs'),
            dashboard_port=int(os.getenv('DASHBOARD_PORT', 8080))
        )
