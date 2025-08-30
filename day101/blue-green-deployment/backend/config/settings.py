from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Blue/Green Deployment Controller"
    debug: bool = True
    api_prefix: str = "/api/v1"
    
    # Environment settings
    blue_port: int = 8001
    green_port: int = 8002
    controller_port: int = 8000
    
    # Health check settings
    health_check_timeout: int = 30
    health_check_interval: int = 5
    max_health_failures: int = 3
    
    # Deployment settings
    deployment_timeout: int = 300
    rollback_timeout: int = 60
    traffic_switch_delay: int = 10
    
    # Database settings
    redis_url: str = "redis://localhost:6379"
    
    # Monitoring
    prometheus_port: int = 9090
    
    class Config:
        env_file = ".env"

settings = Settings()
