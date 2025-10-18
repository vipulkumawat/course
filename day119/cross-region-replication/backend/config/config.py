"""
Configuration settings for cross-region replication system
"""
import os
from typing import Dict, Any

# Environment-based configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Database configuration  
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/cross_region")

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Replication settings
REPLICATION_CONFIG = {
    "max_retry_attempts": 3,
    "retry_delay_seconds": 5,
    "replication_timeout_seconds": 30,
    "conflict_resolution_strategy": "last_write_wins",
    "enable_compression": True,
    "batch_size": 100
}

# Health monitoring settings
HEALTH_CONFIG = {
    "heartbeat_interval_seconds": 5,
    "health_check_timeout_seconds": 10,
    "region_failure_threshold_seconds": 60,
    "recovery_check_interval_seconds": 30
}

# Security settings
SECURITY_CONFIG = {
    "enable_encryption": True,
    "jwt_secret_key": os.getenv("JWT_SECRET_KEY", "dev-secret-key"),
    "token_expiry_hours": 24
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler"
        }
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False
        }
    }
}
