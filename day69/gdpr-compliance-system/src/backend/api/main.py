from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import structlog
from datetime import datetime
import os

from ..models.user_data import Base, UserDataMapping, ErasureRequest
from ..services.erasure_coordinator import ErasureCoordinator
from ..services.data_lineage_tracker import DataLineageTracker
from ..utils.database import get_db, engine

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GDPR Compliance System", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ErasureRequestCreate(BaseModel):
    user_id: str
    request_type: str = "DELETE"

class UserDataTrackingCreate(BaseModel):
    user_id: str
    data_type: str
    storage_location: str
    data_path: str
    metadata: Optional[dict] = None

class ErasureRequestResponse(BaseModel):
    request_id: str
    user_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None

# API Routes
@app.get("/api/")
async def api_root():
    return {"message": "GDPR Compliance System API"}

@app.post("/api/erasure-requests", response_model=ErasureRequestResponse)
async def create_erasure_request(
    request_data: ErasureRequestCreate,
    db: Session = Depends(get_db)
):
    """Create a new erasure request for a user"""
    try:
        coordinator = ErasureCoordinator(db)
        request = await coordinator.create_erasure_request(
            request_data.user_id,
            request_data.request_type
        )
        
        return ErasureRequestResponse(
            request_id=request.id,
            user_id=request.user_id,
            status=request.status,
            created_at=request.created_at.isoformat()
        )
    except Exception as e:
        logger.error("Failed to create erasure request", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/erasure-requests/{request_id}")
async def get_erasure_request(request_id: str, db: Session = Depends(get_db)):
    """Get the status of an erasure request"""
    coordinator = ErasureCoordinator(db)
    request_info = coordinator.get_erasure_request_status(request_id)
    
    if not request_info:
        raise HTTPException(status_code=404, detail="Erasure request not found")
    
    return request_info

@app.post("/api/user-data-tracking")
async def track_user_data(
    tracking_data: UserDataTrackingCreate,
    db: Session = Depends(get_db)
):
    """Track user data location in the system"""
    try:
        tracker = DataLineageTracker(db)
        mapping = tracker.track_user_data(
            tracking_data.user_id,
            tracking_data.data_type,
            tracking_data.storage_location,
            tracking_data.data_path,
            tracking_data.metadata
        )
        
        return {"mapping_id": mapping.id, "message": "User data tracked successfully"}
    except Exception as e:
        logger.error("Failed to track user data", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user-data/{user_id}")
async def get_user_data_locations(user_id: str, db: Session = Depends(get_db)):
    """Get all data locations for a user"""
    tracker = DataLineageTracker(db)
    locations = tracker.get_user_data_locations(user_id)
    
    return {
        "user_id": user_id,
        "data_locations": [
            {
                "id": loc.id,
                "data_type": loc.data_type,
                "storage_location": loc.storage_location,
                "data_path": loc.data_path,
                "created_at": loc.created_at.isoformat()
            }
            for loc in locations
        ]
    }

@app.get("/api/statistics")
async def get_system_statistics(db: Session = Depends(get_db)):
    """Get system statistics"""
    tracker = DataLineageTracker(db)
    stats = tracker.get_data_statistics()
    
    # Add erasure request statistics
    total_requests = db.query(ErasureRequest).count()
    completed_requests = db.query(ErasureRequest).filter(
        ErasureRequest.status == "COMPLETED"
    ).count()
    
    stats.update({
        "total_erasure_requests": total_requests,
        "completed_erasure_requests": completed_requests,
        "completion_rate": (completed_requests / total_requests * 100) if total_requests > 0 else 0
    })
    
    return stats

# Mount static files for React frontend
build_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "build")
if os.path.exists(build_path):
    app.mount("/static", StaticFiles(directory=os.path.join(build_path, "static")), name="static")

# Serve React app
@app.get("/")
async def serve_react_app():
    """Serve the React frontend"""
    index_path = os.path.join(build_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": "React frontend not built. Run 'npm run build' first."}

# Catch-all route for React Router
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """Catch-all route for React Router"""
    # Don't interfere with API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Try to serve static files first
    static_path = os.path.join(build_path, full_path)
    if os.path.exists(static_path) and os.path.isfile(static_path):
        return FileResponse(static_path)
    
    # Fall back to serving index.html for React Router
    index_path = os.path.join(build_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": "React frontend not built. Run 'npm run build' first."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
