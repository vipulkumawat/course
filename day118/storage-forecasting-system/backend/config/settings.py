import os
from typing import Optional

class Settings:
    # Database settings
    INFLUXDB_URL: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    INFLUXDB_TOKEN: str = os.getenv("INFLUXDB_TOKEN", "admin-token")
    INFLUXDB_ORG: str = os.getenv("INFLUXDB_ORG", "storage-org")
    INFLUXDB_BUCKET: str = os.getenv("INFLUXDB_BUCKET", "storage-metrics")
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Forecasting settings
    FORECAST_HORIZONS: list = [30, 60, 90]  # days
    MODEL_RETRAIN_INTERVAL: int = 24  # hours
    DATA_COLLECTION_INTERVAL: int = 300  # seconds
    
    # Storage cost settings (per GB per month)
    STORAGE_COST_PRIMARY: float = 0.023
    STORAGE_COST_REPLICA: float = 0.019
    STORAGE_COST_ARCHIVE: float = 0.012

settings = Settings()
