#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import logging
import os
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Log Processor",
    description="Distributed Log Processing Service",
    version=os.getenv("VERSION", "1.0.0")
)

# Environment info
ENVIRONMENT = os.getenv("ENVIRONMENT", "unknown")
VERSION = os.getenv("VERSION", "1.0.0")
NEW_FEATURE = os.getenv("NEW_FEATURE", "disabled") == "enabled"

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    source: str

class ProcessResult(BaseModel):
    status: str
    log_id: str
    processed_at: str
    environment: str
    version: str
    new_feature_enabled: bool

@app.get("/")
async def root():
    return {
        "service": "Log Processor",
        "environment": ENVIRONMENT,
        "version": VERSION,
        "new_feature": NEW_FEATURE,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "api": "healthy",
            "processing": "healthy",
            "storage": "healthy"
        }
    }

@app.get("/metrics")
async def get_metrics():
    # Simulate metrics response
    return {
        "requests_total": 1234,
        "requests_per_second": 45.6,
        "response_time_ms": 23.4,
        "error_rate": 0.01,
        "environment": ENVIRONMENT,
        "version": VERSION
    }

@app.post("/process-log", response_model=ProcessResult)
async def process_log(log_entry: LogEntry):
    """Process a log entry"""
    try:
        # Simulate log processing
        logger.info(f"Processing log: {log_entry.level} - {log_entry.message}")
        
        # Generate log ID
        log_id = f"{ENVIRONMENT}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Simulate processing logic
        if NEW_FEATURE:
            # Enhanced processing with new feature
            logger.info("🚀 Processing with new feature enabled")
        
        return ProcessResult(
            status="processed",
            log_id=log_id,
            processed_at=datetime.now().isoformat(),
            environment=ENVIRONMENT,
            version=VERSION,
            new_feature_enabled=NEW_FEATURE
        )
        
    except Exception as e:
        logger.error(f"Failed to process log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info")
async def get_info():
    """Get detailed service information"""
    return {
        "service": "Log Processor",
        "environment": ENVIRONMENT,
        "version": VERSION,
        "features": {
            "new_feature": NEW_FEATURE,
            "processing_enabled": True,
            "health_checks": True
        },
        "uptime": "running",
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "log_processor:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
