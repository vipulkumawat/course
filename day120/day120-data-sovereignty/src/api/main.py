"""FastAPI application for data sovereignty compliance"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classification.classifier import DataClassifier
from enforcement.policy_engine import PolicyEngine
from audit.audit_logger import ComplianceAuditLogger

app = FastAPI(title="Data Sovereignty Compliance API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
classifier = DataClassifier()
policy_engine = PolicyEngine()
audit_logger = ComplianceAuditLogger()

class LogEntry(BaseModel):
    id: str
    message: str
    level: str
    service: str
    ip_address: Optional[str] = None
    user_location: Optional[str] = None
    user_id: Optional[str] = None

class StorageRequest(BaseModel):
    log_entry: Dict
    target_region: str

class TransferRequest(BaseModel):
    log_entry: Dict
    source_region: str
    target_region: str

@app.get("/")
async def root():
    return {"status": "Data Sovereignty Compliance API", "version": "1.0"}

@app.post("/classify")
async def classify_log(log_entry: LogEntry):
    """Classify log entry with sovereignty metadata"""
    try:
        classification = classifier.classify_log(log_entry.dict())
        audit_logger.log_classification(log_entry.id, classification)
        return {
            "log_id": log_entry.id,
            "classification": classification,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate/storage")
async def validate_storage(request: StorageRequest):
    """Validate if log can be stored in target region"""
    try:
        # First classify
        classification = classifier.classify_log(request.log_entry)
        
        # Then validate
        decision = policy_engine.validate_storage(
            classification,
            request.target_region
        )
        
        # Log audit event
        audit_logger.log_storage_decision(
            request.log_entry.get('id', 'unknown'),
            decision,
            request.target_region
        )
        
        return {
            "log_id": request.log_entry.get('id'),
            "classification": classification,
            "decision": decision,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate/transfer")
async def validate_transfer(request: TransferRequest):
    """Validate cross-border data transfer"""
    try:
        # Classify
        classification = classifier.classify_log(request.log_entry)
        
        # Validate transfer
        decision = policy_engine.validate_transfer(
            classification,
            request.source_region,
            request.target_region
        )
        
        # Log audit event
        audit_logger.log_transfer_decision(
            request.log_entry.get('id', 'unknown'),
            decision,
            request.source_region,
            request.target_region
        )
        
        return {
            "log_id": request.log_entry.get('id'),
            "classification": classification,
            "decision": decision,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/compliance/report")
async def get_compliance_report(hours: int = 24):
    """Generate compliance report"""
    try:
        report = audit_logger.generate_compliance_report(hours)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/compliance/violations")
async def get_violations():
    """Get all compliance violations"""
    try:
        violations = audit_logger.get_all_violations()
        return {
            "total_violations": len(violations),
            "violations": violations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "data-sovereignty-compliance"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
