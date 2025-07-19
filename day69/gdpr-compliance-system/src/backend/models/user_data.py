from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class UserDataMapping(Base):
    __tablename__ = "user_data_mappings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    data_type = Column(String, nullable=False)
    storage_location = Column(String, nullable=False)
    data_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    data_metadata = Column(Text)

class ErasureRequest(Base):
    __tablename__ = "erasure_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    request_type = Column(String, nullable=False)  # DELETE, ANONYMIZE
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    data_metadata = Column(Text)

class ErasureAuditLog(Base):
    __tablename__ = "erasure_audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    erasure_request_id = Column(String, ForeignKey("erasure_requests.id"))
    action = Column(String, nullable=False)
    component = Column(String, nullable=False)
    data_location = Column(String, nullable=False)
    records_affected = Column(Integer, default=0)
    status = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text)
    
    erasure_request = relationship("ErasureRequest", back_populates="audit_logs")

ErasureRequest.audit_logs = relationship("ErasureAuditLog", back_populates="erasure_request")
