import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Webhook Integration System"
    database_url: str = "sqlite:///./webhook_system.db"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = ""  # Set via SECRET_KEY environment variable
    webhook_timeout: int = 30
    max_retry_attempts: int = 3
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    model_config = {"env_file": ".env"}

settings = Settings()
