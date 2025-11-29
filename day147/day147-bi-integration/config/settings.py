from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_VERSION: str = "v1"
    
    # Database Configuration
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = ""  # Set via environment variable INFLUXDB_TOKEN
    INFLUXDB_ORG: str = "log-processing"
    INFLUXDB_BUCKET: str = "metrics"
    
    TIMESCALE_HOST: str = "localhost"
    TIMESCALE_PORT: int = 5432
    TIMESCALE_DB: str = "metrics"
    TIMESCALE_USER: str = "postgres"
    TIMESCALE_PASSWORD: str = ""  # Set via environment variable TIMESCALE_PASSWORD
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 300  # 5 minutes
    
    # OAuth Configuration
    JWT_SECRET_KEY: str = ""  # Set via environment variable JWT_SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Export Configuration
    EXPORT_BASE_PATH: str = "./exports"
    EXPORT_FORMATS: list = ["csv", "parquet"]
    
    # Performance Configuration
    MAX_QUERY_RANGE_DAYS: int = 90
    DEFAULT_PAGE_SIZE: int = 1000
    MAX_PAGE_SIZE: int = 10000
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
