"""
Pydantic models for API validation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SearchQueryParams(BaseModel):
    query_text: str = Field(..., description="Search query string")
    time_range: Dict[str, Any] = Field(..., description="Time range parameters")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Additional filters")
    service_filters: List[str] = Field(default_factory=list, description="Service name filters")
    log_level_filters: List[str] = Field(default_factory=list, description="Log level filters")
    sort_by: str = Field(default="timestamp", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order")
    limit: int = Field(default=100, description="Result limit")

class VisualizationConfig(BaseModel):
    chart_type: str = Field(..., description="Type of chart")
    x_axis: str = Field(..., description="X-axis field")
    y_axis: str = Field(..., description="Y-axis field")
    grouping: Optional[str] = Field(None, description="Grouping field")
    time_granularity: str = Field(default="minute", description="Time aggregation level")
    colors: List[str] = Field(default_factory=list, description="Chart colors")

class SavedSearchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    query_params: SearchQueryParams
    visualization_config: Optional[VisualizationConfig] = None
    folder: str = Field(default="default")
    tags: List[str] = Field(default_factory=list)
    is_shared: bool = Field(default=False)
    shared_with: List[str] = Field(default_factory=list)

class SavedSearchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    query_params: Optional[SearchQueryParams] = None
    visualization_config: Optional[VisualizationConfig] = None
    folder: Optional[str] = None
    tags: Optional[List[str]] = None
    is_shared: Optional[bool] = None
    shared_with: Optional[List[str]] = None

class SavedSearchResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    user_id: str
    query_params: Dict[str, Any]
    visualization_config: Optional[Dict[str, Any]]
    folder: str
    tags: List[str]
    usage_count: int
    is_shared: bool
    shared_with: List[str]
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime]

class ConditionType(str, Enum):
    THRESHOLD = "threshold"
    PATTERN = "pattern"
    ANOMALY = "anomaly"

class ComparisonOperator(str, Enum):
    GREATER_THAN = ">"
    LESS_THAN = "<"
    EQUAL = "="
    NOT_EQUAL = "!="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"

class NotificationChannel(str, Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    IN_APP = "in_app"

class AlertCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    saved_search_id: str
    condition_type: ConditionType
    threshold_value: Optional[str] = None
    comparison_operator: Optional[ComparisonOperator] = None
    time_window_minutes: int = Field(default=5, ge=1, le=1440)
    notification_channels: List[NotificationChannel]
    notification_emails: List[str] = Field(default_factory=list)
    webhook_url: Optional[str] = None
    cooldown_minutes: int = Field(default=15, ge=1, le=1440)

    @validator('notification_emails')
    def validate_emails(cls, v, values):
        if NotificationChannel.EMAIL in values.get('notification_channels', []):
            if not v:
                raise ValueError('Email addresses required when email notifications enabled')
        return v

    @validator('webhook_url')
    def validate_webhook(cls, v, values):
        if NotificationChannel.WEBHOOK in values.get('notification_channels', []):
            if not v:
                raise ValueError('Webhook URL required when webhook notifications enabled')
        return v

class AlertUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    condition_type: Optional[ConditionType] = None
    threshold_value: Optional[str] = None
    comparison_operator: Optional[ComparisonOperator] = None
    time_window_minutes: Optional[int] = Field(None, ge=1, le=1440)
    notification_channels: Optional[List[NotificationChannel]] = None
    notification_emails: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    cooldown_minutes: Optional[int] = Field(None, ge=1, le=1440)
    is_active: Optional[bool] = None

class AlertResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    user_id: str
    saved_search_id: str
    condition_type: str
    threshold_value: Optional[str]
    comparison_operator: Optional[str]
    time_window_minutes: int
    notification_channels: List[str]
    notification_emails: List[str]
    webhook_url: Optional[str]
    cooldown_minutes: int
    is_active: bool
    last_triggered: Optional[datetime]
    trigger_count: int
    created_at: datetime
    updated_at: datetime

class NotificationResponse(BaseModel):
    id: str
    alert_id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    channel: str
    status: str
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
