from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..models.user_data import ErasureRequest, ErasureAuditLog, UserDataMapping
from .data_lineage_tracker import DataLineageTracker
from .anonymization_engine import AnonymizationEngine
import structlog
from datetime import datetime
import asyncio

logger = structlog.get_logger()

class ErasureCoordinator:
    def __init__(self, db: Session):
        self.db = db
        self.data_tracker = DataLineageTracker(db)
        self.anonymization_engine = AnonymizationEngine()
    
    async def create_erasure_request(self, user_id: str, 
                                   request_type: str = "DELETE") -> ErasureRequest:
        """Create a new erasure request"""
        request = ErasureRequest(
            user_id=user_id,
            request_type=request_type,
            status="PENDING"
        )
        
        self.db.add(request)
        self.db.commit()
        
        logger.info("Erasure request created", 
                   request_id=request.id,
                   user_id=user_id,
                   request_type=request_type)
        
        # Start processing asynchronously
        asyncio.create_task(self.process_erasure_request(request.id))
        
        return request
    
    async def process_erasure_request(self, request_id: str):
        """Process erasure request through all stages"""
        request = self.db.query(ErasureRequest).filter(
            ErasureRequest.id == request_id
        ).first()
        
        if not request:
            logger.error("Erasure request not found", request_id=request_id)
            return
        
        try:
            # Update status to DISCOVERING
            request.status = "DISCOVERING"
            self.db.commit()
            
            # Discover user data
            data_locations = self.data_tracker.get_user_data_locations(request.user_id)
            
            # Update status to EXECUTING
            request.status = "EXECUTING"
            self.db.commit()
            
            # Execute erasure for each location
            for location in data_locations:
                await self._execute_erasure_for_location(request, location)
            
            # Update status to VERIFYING
            request.status = "VERIFYING"
            self.db.commit()
            
            # Verify erasure completion
            verification_success = await self._verify_erasure_completion(request)
            
            # Update final status
            request.status = "COMPLETED" if verification_success else "FAILED"
            request.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info("Erasure request completed", 
                       request_id=request_id,
                       status=request.status)
            
        except Exception as e:
            request.status = "FAILED"
            self.db.commit()
            logger.error("Erasure request failed", 
                        request_id=request_id,
                        error=str(e))
    
    async def _execute_erasure_for_location(self, request: ErasureRequest, 
                                          location: UserDataMapping):
        """Execute erasure for a specific data location"""
        try:
            if request.request_type == "DELETE":
                records_affected = await self._delete_user_data(location)
            else:  # ANONYMIZE
                records_affected = await self._anonymize_user_data(location)
            
            # Log the action
            audit_log = ErasureAuditLog(
                erasure_request_id=request.id,
                action=request.request_type,
                component=location.storage_location,
                data_location=location.data_path,
                records_affected=records_affected,
                status="SUCCESS"
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            # Log the failure
            audit_log = ErasureAuditLog(
                erasure_request_id=request.id,
                action=request.request_type,
                component=location.storage_location,
                data_location=location.data_path,
                records_affected=0,
                status="FAILED",
                details=str(e)
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
            logger.error("Erasure failed for location", 
                        location=location.storage_location,
                        error=str(e))
    
    async def _delete_user_data(self, location: UserDataMapping) -> int:
        """Delete user data from specified location"""
        # Simulate data deletion
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # In real implementation, this would:
        # 1. Connect to the specific storage system
        # 2. Execute deletion queries/operations
        # 3. Return the number of records affected
        
        return 1  # Simulated count
    
    async def _anonymize_user_data(self, location: UserDataMapping) -> int:
        """Anonymize user data at specified location"""
        # Simulate data anonymization
        await asyncio.sleep(0.1)
        
        # In real implementation, this would:
        # 1. Connect to the specific storage system
        # 2. Apply anonymization transformations
        # 3. Return the number of records affected
        
        return 1  # Simulated count
    
    async def _verify_erasure_completion(self, request: ErasureRequest) -> bool:
        """Verify that erasure was completed successfully"""
        # Check audit logs for any failures
        failed_logs = self.db.query(ErasureAuditLog).filter(
            ErasureAuditLog.erasure_request_id == request.id,
            ErasureAuditLog.status == "FAILED"
        ).count()
        
        return failed_logs == 0
    
    def get_erasure_request_status(self, request_id: str) -> Optional[Dict]:
        """Get the status of an erasure request"""
        request = self.db.query(ErasureRequest).filter(
            ErasureRequest.id == request_id
        ).first()
        
        if not request:
            return None
        
        audit_logs = self.db.query(ErasureAuditLog).filter(
            ErasureAuditLog.erasure_request_id == request_id
        ).all()
        
        return {
            "request_id": request.id,
            "user_id": request.user_id,
            "status": request.status,
            "created_at": request.created_at.isoformat(),
            "completed_at": request.completed_at.isoformat() if request.completed_at else None,
            "audit_logs": [
                {
                    "action": log.action,
                    "component": log.component,
                    "records_affected": log.records_affected,
                    "status": log.status,
                    "timestamp": log.timestamp.isoformat()
                }
                for log in audit_logs
            ]
        }
