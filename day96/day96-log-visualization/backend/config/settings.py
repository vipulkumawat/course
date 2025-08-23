import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost:5432/logdb"
    redis_url: str = "redis://localhost:6379"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    websocket_port: int = 8001
    cors_origins: list = ["http://localhost:3000", "http://localhost:3001"]
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
