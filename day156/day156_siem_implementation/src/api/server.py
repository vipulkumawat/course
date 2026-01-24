"""
FastAPI server for SIEM REST API
"""
import asyncio
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import List, Dict
import yaml
import structlog
import json
import time

from src.siem.engine import SIEMEngine, SecurityEvent, EventType
from src.processors.normalizer import EventNormalizer

logger = structlog.get_logger()

# Get the project root directory (parent of src)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Load configuration
config_path = PROJECT_ROOT / 'config' / 'siem_config.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

app = FastAPI(title="SIEM API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SIEM engine
siem_engine = SIEMEngine(config)
normalizer = EventNormalizer()

# WebSocket connections for real-time updates
active_websockets: List[WebSocket] = []


@app.on_event("startup")
async def startup_event():
    """Initialize SIEM on startup"""
    await siem_engine.initialize()
    logger.info("SIEM API server started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await siem_engine.shutdown()
    logger.info("SIEM API server stopped")


@app.get("/")
async def root():
    """Root endpoint - redirects to dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")


@app.get("/health")
async def health_check():
    """Detailed health check"""
    stats = await siem_engine.get_statistics()
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "statistics": stats
    }


@app.post("/api/events/ingest")
async def ingest_event(event_data: Dict):
    """Ingest a raw log event"""
    try:
        # Normalize based on log type
        log_type = event_data.get('type', 'access')
        
        if log_type == 'auth':
            security_event = normalizer.normalize_auth_log(event_data)
        elif log_type == 'access':
            security_event = normalizer.normalize_access_log(event_data)
        elif log_type == 'admin':
            security_event = normalizer.normalize_admin_log(event_data)
        else:
            raise ValueError(f"Unknown log type: {log_type}")
        
        if not security_event:
            raise HTTPException(status_code=400, detail="Failed to normalize event")
        
        # Process through SIEM
        incident = await siem_engine.process_event(security_event)
        
        # Notify WebSocket clients
        if incident:
            await broadcast_incident(incident)
        
        return {
            "status": "processed",
            "event_id": security_event.event_id,
            "incident_created": incident is not None,
            "incident_id": incident.incident_id if incident else None
        }
        
    except Exception as e:
        logger.error("Error ingesting event", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/incidents")
async def get_incidents(limit: int = 50):
    """Get recent security incidents"""
    try:
        incidents = await siem_engine.get_recent_incidents(limit)
        return {
            "total": len(incidents),
            "incidents": incidents
        }
    except Exception as e:
        logger.error("Error retrieving incidents", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statistics")
async def get_statistics():
    """Get SIEM statistics"""
    try:
        stats = await siem_engine.get_statistics()
        return stats
    except Exception as e:
        logger.error("Error retrieving statistics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/incidents")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time incident updates"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_websockets.remove(websocket)


async def broadcast_incident(incident):
    """Broadcast incident to all connected WebSocket clients"""
    incident_data = json.dumps(incident.to_dict())
    
    for websocket in active_websockets[:]:  # Copy list to avoid modification during iteration
        try:
            await websocket.send_text(incident_data)
        except:
            active_websockets.remove(websocket)


# Serve dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve SIEM dashboard HTML"""
    try:
        dashboard_path = PROJECT_ROOT / 'web' / 'templates' / 'dashboard.html'
        with open(dashboard_path, 'r') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError as e:
        logger.error(f"Dashboard file not found: {e}")
        return HTMLResponse(content=f"<h1>Dashboard not found</h1><p>Path: {dashboard_path}</p>", status_code=404)
