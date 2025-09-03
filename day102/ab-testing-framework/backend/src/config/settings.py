import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/ab_testing"
    redis_url: str = "redis://localhost:6379/0"
    
    # Feature Flags
    feature_flag_cache_ttl: int = 300  # 5 minutes
    default_rollout_percentage: float = 0.0
    
    # Experiments
    min_sample_size: int = 1000
    significance_threshold: float = 0.05
    statistical_power: float = 0.8
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list = ["http://localhost:3000", "http://localhost:3001"]
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
