"""Windows Event Log Agent Configuration"""
import os
from typing import Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class EventLogConfig(BaseSettings):
    """Event Log Collection Configuration"""
    
    # Event Log Channels
    channels: List[str] = Field(default=[
        "System",
        "Application", 
        "Security",
        "Setup",
        "Microsoft-Windows-Kernel-General/Operational"
    ])
    
    # Filtering configuration
    event_levels: List[str] = Field(default=["Error", "Warning", "Information"])
    max_events_per_batch: int = Field(default=100)
    batch_timeout_seconds: int = Field(default=10)
    
    # Performance settings
    subscription_mode: str = Field(default="push")  # push or pull
    buffer_size_mb: int = Field(default=50)
    concurrent_channels: int = Field(default=5)
    
    # Storage and state
    bookmark_file: str = Field(default="data/bookmarks/event_bookmarks.json")
    state_file: str = Field(default="data/state/agent_state.json")
    cache_dir: str = Field(default="data/cache")
    
    # Transport configuration
    transport_url: str = Field(default="http://localhost:8080/api/v1/logs")
    transport_timeout: int = Field(default=30)
    retry_attempts: int = Field(default=3)
    
    # Security settings
    enable_tls: bool = Field(default=True)
    cert_verify: bool = Field(default=True)
    api_key: Optional[str] = Field(default=None)
    
    # Monitoring
    health_check_interval: int = Field(default=60)
    metrics_port: int = Field(default=9090)
    log_level: str = Field(default="INFO")
    
    class Config:
        env_prefix = "WINDOWS_AGENT_"
        env_file = ".env"

# Global configuration instance
config = EventLogConfig()
