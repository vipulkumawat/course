"""
Database models for saved searches and alerts
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class SavedSearch(Base):
    __tablename__ = "saved_searches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    user_id = Column(String(100), nullable=False)
    query_params = Column(JSON, nullable=False)  # Store complete search context
    visualization_config = Column(JSON)  # Chart settings, display preferences
    folder = Column(String(100), default="default")
    tags = Column(JSON, default=list)
    usage_count = Column(Integer, default=0)
    is_shared = Column(Boolean, default=False)
    shared_with = Column(JSON, default=list)  # List of user IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime)
    
    # Relationship to alerts
    alerts = relationship("Alert", back_populates="saved_search", cascade="all, delete-orphan")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    user_id = Column(String(100), nullable=False)
    saved_search_id = Column(String, ForeignKey("saved_searches.id"), nullable=False)
    
    # Alert conditions
    condition_type = Column(String(50), nullable=False)  # threshold, pattern, anomaly
    threshold_value = Column(String(100))
    comparison_operator = Column(String(10))  # >, <, =, !=, contains
    time_window_minutes = Column(Integer, default=5)
    
    # Notification settings
    notification_channels = Column(JSON, default=list)  # email, webhook, in_app
    notification_emails = Column(JSON, default=list)
    webhook_url = Column(String(500))
    cooldown_minutes = Column(Integer, default=15)
    
    # State management
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    saved_search = relationship("SavedSearch", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert", cascade="all, delete-orphan")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String, ForeignKey("alerts.id"), nullable=False)
    user_id = Column(String(100), nullable=False)
    
    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # alert, info, warning, error
    channel = Column(String(50), nullable=False)  # email, webhook, in_app
    
    # Context data
    trigger_data = Column(JSON)  # Log data that triggered the alert
    related_logs = Column(JSON)  # Additional context logs
    
    # Delivery tracking
    status = Column(String(20), default="pending")  # pending, sent, delivered, failed
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    alert = relationship("Alert", back_populates="notifications")

class SearchFolder(Base):
    __tablename__ = "search_folders"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    user_id = Column(String(100), nullable=False)
    parent_folder_id = Column(String, ForeignKey("search_folders.id"))
    description = Column(Text)
    color = Column(String(7), default="#3B82F6")  # Hex color
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for nested folders
    subfolders = relationship("SearchFolder", backref="parent", remote_side=[id])
