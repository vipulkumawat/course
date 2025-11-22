"""Configuration management for ticket creation system"""

from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # JIRA Configuration
    jira_url: str = "https://demo-jira.atlassian.net"
    jira_username: str = ""  # Set via JIRA_USERNAME env var
    jira_api_token: str = ""  # Set via JIRA_API_TOKEN env var
    jira_project_key: str = "DEMO"

    # ServiceNow Configuration
    servicenow_url: str = "https://demo.service-now.com"
    servicenow_username: str = ""  # Set via SERVICENOW_USERNAME env var
    servicenow_password: str = ""  # Set via SERVICENOW_PASSWORD env var
    servicenow_table: str = "incident"

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"

    # Event Processing
    event_batch_size: int = 100
    event_processing_interval: int = 5  # seconds
    duplicate_detection_window: int = 300  # seconds

    # Ticket Creation Rules
    severity_mapping: Dict[str, str] = {
        "critical": "1",  # High priority
        "error": "2",  # Medium priority
        "warning": "3",  # Low priority
        "info": "4",  # Informational
    }

    # Team routing rules
    team_routing: Dict[str, str] = {
        "database": "JIRA",
        "api": "JIRA",
        "infrastructure": "ServiceNow",
        "security": "ServiceNow",
    }

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
