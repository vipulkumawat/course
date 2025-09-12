from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class ConfigScope(str, Enum):
    GLOBAL = "global"
    TENANT = "tenant" 
    USER = "user"

class ConfigState(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"
    ARCHIVED = "archived"

class ConfigEntry(BaseModel):
    key: str
    value: Any
    scope: ConfigScope
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    state: ConfigState = ConfigState.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    description: Optional[str] = None
    schema_version: str = "1.0"

class TenantConfigSchema(BaseModel):
    log_retention_days: int = Field(default=30, ge=1, le=2555)  # Max 7 years
    max_log_rate_per_second: int = Field(default=1000, ge=1, le=100000)
    alert_email: str = Field(default="admin@tenant.com", pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    custom_parsing_rules: List[str] = Field(default_factory=list)
    webhook_endpoints: List[str] = Field(default_factory=list)
    alert_thresholds: Dict[str, float] = Field(default_factory=lambda: {
        "error_rate": 0.05,
        "latency_p99": 1000,
        "memory_usage": 0.8
    })
    integration_configs: Dict[str, Dict] = Field(default_factory=dict)
    ui_preferences: Dict[str, Any] = Field(default_factory=lambda: {
        "theme": "light",
        "dashboard_refresh_rate": 30,
        "default_time_range": "1h"
    })

    @field_validator('webhook_endpoints')
    @classmethod
    def validate_webhook_urls(cls, v):
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        for url in v:
            if not url_pattern.match(url):
                raise ValueError(f'Invalid webhook URL: {url}')
        return v

class ConfigChange(BaseModel):
    tenant_id: str
    config_key: str
    old_value: Any
    new_value: Any
    changed_by: str
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    change_reason: Optional[str] = None
