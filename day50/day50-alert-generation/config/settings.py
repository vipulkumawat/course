"""Configuration settings for the alert generation system."""
import os
from pydantic_settings import BaseSettings
from typing import List, Dict

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/alertdb"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Alert Engine
    PATTERN_CHECK_INTERVAL: int = 5  # seconds
    CORRELATION_WINDOW: int = 300  # 5 minutes
    MAX_ALERTS_PER_MINUTE: int = 10
    
    # Notification
    NOTIFICATION_CHANNELS: List[str] = ["email", "slack", "webhook"]
    EMAIL_SMTP_HOST: str = "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 587
    SLACK_WEBHOOK_URL: str = ""
    
    # Patterns
    DEFAULT_PATTERNS: Dict = {
        "auth_failure": {
            "pattern": r"authentication\s+failed|login\s+failed|auth\s+error",
            "threshold": 5,
            "window": 60,
            "severity": "high"
        },
        "database_error": {
            "pattern": r"database\s+error|connection\s+timeout|query\s+failed",
            "threshold": 3,
            "window": 120,
            "severity": "critical"
        },
        "api_error": {
            "pattern": r"HTTP\s+5\d\d|internal\s+server\s+error|service\s+unavailable",
            "threshold": 10,
            "window": 300,
            "severity": "medium"
        }
    }
    
    class Config:
        env_file = ".env"

settings = Settings()
