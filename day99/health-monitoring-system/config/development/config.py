import os
from typing import Dict, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application Settings
    app_name: str = "Health Monitoring System"
    version: str = "1.0.0"
    debug: bool = True
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # Database Settings
    database_url: str = "sqlite:///./health_monitoring.db"
    
    # Redis Settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Health Check Settings
    health_check_interval: int = 30  # seconds
    metric_retention_days: int = 30
    alert_check_interval: int = 60   # seconds
    
    # Component Registration
    component_timeout: int = 120     # seconds
    max_component_failures: int = 3
    
    # Alert Settings
    alert_cooldown: int = 300        # seconds
    max_alerts_per_hour: int = 100
    
    # Monitoring Thresholds
    cpu_warning_threshold: float = 70.0
    cpu_critical_threshold: float = 90.0
    memory_warning_threshold: float = 80.0
    memory_critical_threshold: float = 95.0
    disk_warning_threshold: float = 85.0
    disk_critical_threshold: float = 95.0
    
    class Config:
        env_file = ".env"

settings = Settings()
