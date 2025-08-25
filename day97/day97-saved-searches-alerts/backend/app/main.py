"""
Day 97: Main FastAPI application for saved searches and alerts
"""
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import logging
from datetime import datetime
import json

from .core.database import init_db, get_db
from .api.routes import saved_searches, alerts, notifications
from .services.alert_engine import AlertEngine
from .services.notification_service import NotificationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
alert_engine = None
notification_service = None
active_connections = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global alert_engine, notification_service
    
    # Startup
    logger.info("🚀 Starting Saved Searches and Alerts System")
    await init_db()
    
    # Initialize services
    notification_service = NotificationService()
    alert_engine = AlertEngine(notification_service)
    
    # Start background tasks
    asyncio.create_task(alert_engine.start_monitoring())
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down system")
    if alert_engine:
        await alert_engine.stop_monitoring()

app = FastAPI(
    title="Log Processing - Saved Searches & Alerts",
    version="1.0.0",
    description="Advanced search management and real-time alerting system",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(saved_searches.router, prefix="/api/searches", tags=["searches"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])

# WebSocket for real-time notifications
@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "alert_engine": "active" if alert_engine else "inactive",
            "notification_service": "active" if notification_service else "inactive",
            "active_connections": len(active_connections)
        }
    }

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Saved Searches and Alerts API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
