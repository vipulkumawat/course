from fastapi import FastAPI, HTTPException, WebSocket, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import logging
from datetime import datetime
import json
import uvicorn

from core.deployment_controller import DeploymentController
from api.endpoints import router as api_router
from core.health_checker import HealthChecker
from core.traffic_router import TrafficRouter
from models.deployment import DeploymentStatus, Environment
from services.websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Blue/Green Deployment Controller",
    description="Zero-downtime deployment system for distributed log processing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
deployment_controller = DeploymentController()
health_checker = HealthChecker()
traffic_router = TrafficRouter()
websocket_manager = WebSocketManager()

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("🚀 Starting Blue/Green Deployment Controller")
    
    # Initialize environments
    await deployment_controller.initialize_environments()
    
    # Start background health monitoring
    asyncio.create_task(health_checker.start_monitoring())
    
    # Initialize traffic router
    await traffic_router.initialize()
    
    logger.info("✅ System initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown"""
    logger.info("🛑 Shutting down deployment controller")
    await deployment_controller.cleanup()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Blue/Green Deployment Controller",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return await health_checker.get_overall_health()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket_manager.connect(websocket)
    logger.info("🔌 WebSocket client connected")
    
    try:
        # Wait a moment for the connection to stabilize
        await asyncio.sleep(0.5)
        
        while True:
            try:
                # Send periodic updates
                status = await deployment_controller.get_status()
                await websocket_manager.send_personal_message(
                    status.model_dump_json(), websocket
                )
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("🔌 WebSocket client disconnecting")
        websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
