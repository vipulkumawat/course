"""Configuration settings"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Playbook settings
    max_concurrent_playbooks: int = 10
    default_action_timeout: int = 30
    default_max_retries: int = 2
    
    # Alert settings
    email_enabled: bool = True
    slack_enabled: bool = True
    pagerduty_enabled: bool = True
    
    # Evidence collection
    forensics_base_path: str = "/forensics"
    preserve_evidence: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()
