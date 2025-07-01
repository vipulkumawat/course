from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    app_name: str = "Analytics Dashboard"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: str = f"redis://{redis_host}:{redis_port}/{redis_db}"
    
    # WebSocket configuration
    websocket_heartbeat_interval: int = 30
    websocket_timeout: int = 60
    
    # Analytics configuration
    metrics_batch_size: int = 100
    trend_calculation_window: int = 300  # 5 minutes
    anomaly_threshold: float = 2.0  # Standard deviations
    
    # Dashboard configuration
    max_chart_points: int = 1000
    default_time_range: int = 3600  # 1 hour
    refresh_interval: int = 5000  # 5 seconds
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    allowed_origins: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    
    class Config:
        env_file = ".env"

settings = Settings() 