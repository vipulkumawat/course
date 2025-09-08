import os
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class BackupStrategy(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class StorageBackend(Enum):
    LOCAL = "local"
    S3 = "s3"
    REDIS = "redis"

@dataclass
class BackupConfig:
    # Scheduling configuration
    full_backup_interval: str = "0 2 * * 0"  # Weekly at 2 AM Sunday
    incremental_interval: str = "0 */6 * * *"  # Every 6 hours
    differential_interval: str = "0 1 * * *"  # Daily at 1 AM
    
    # Storage configuration
    storage_backend: StorageBackend = StorageBackend.LOCAL
    backup_directory: str = "backups"
    retention_days: int = 30
    max_concurrent_backups: int = 3
    
    # Compression and encryption
    enable_compression: bool = True
    enable_encryption: bool = False
    encryption_key: str = os.getenv("BACKUP_ENCRYPTION_KEY", "default-key-change-in-prod")
    
    # Validation settings
    validation_enabled: bool = True
    sample_validation_ratio: float = 0.1  # Validate 10% of backed up data
    checksum_algorithm: str = "sha256"
    
    # Recovery settings
    recovery_timeout_minutes: int = 30
    parallel_recovery_streams: int = 4
    
    # Monitoring
    alert_on_failure: bool = True
    dashboard_port: int = 8105
    websocket_port: int = 8106

config = BackupConfig()
