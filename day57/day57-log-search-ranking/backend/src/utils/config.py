"""
Configuration management
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Search Configuration
    max_search_results: int = 100
    search_timeout_seconds: int = 30
    
    # Ranking Configuration
    enable_temporal_ranking: bool = True
    enable_context_ranking: bool = True
    
    # Redis Configuration (for future use)
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()
