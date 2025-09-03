from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON, Text
from sqlalchemy.sql import func
from config.database import Base

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    is_enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Float, default=0.0)
    targeting_rules = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Experiment(Base):
    __tablename__ = "experiments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    status = Column(String(20), default="draft")  # draft, running, paused, completed
    feature_flag_name = Column(String(100), nullable=False)
    control_percentage = Column(Float, default=50.0)
    treatment_percentage = Column(Float, default=50.0)
    success_metrics = Column(JSON, default=list)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserAssignment(Base):
    __tablename__ = "user_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    experiment_id = Column(Integer, nullable=False, index=True)
    variant = Column(String(50), nullable=False)  # control, treatment
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
