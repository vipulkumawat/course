from pydantic import BaseSettings
from typing import Dict, Any
import os

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "sqlite:///./tiered_storage.db"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Storage tier settings
    HOT_STORAGE_PATH: str = "./data/hot"
    WARM_STORAGE_PATH: str = "./data/warm"
    COLD_STORAGE_PATH: str = "./data/cold"
    ARCHIVE_STORAGE_PATH: str = "./data/archive"
    
    # Migration policies (in days)
    HOT_TO_WARM_DAYS: int = 7
    WARM_TO_COLD_DAYS: int = 30
    COLD_TO_ARCHIVE_DAYS: int = 365
    
    # Performance settings
    MIGRATION_BATCH_SIZE: int = 1000
    MIGRATION_INTERVAL_MINUTES: int = 60
    
    # Cost settings (per TB per month)
    HOT_TIER_COST: float = 200.0
    WARM_TIER_COST: float = 50.0
    COLD_TIER_COST: float = 10.0
    ARCHIVE_TIER_COST: float = 1.0
    
    class Config:
        env_file = ".env"

settings = Settings()
