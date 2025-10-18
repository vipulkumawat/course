"""
Cross-Region Data Replication System
Main FastAPI Application Entry Point
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from replication.coordinator import ReplicationCoordinator
from replication.region_manager import RegionManager
from monitoring.health_monitor import HealthMonitor
from routing.client_router import ClientRouter
from api.routes import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global components
replication_coordinator: ReplicationCoordinator = None
region_manager: RegionManager = None
health_monitor: HealthMonitor = None
client_router: ClientRouter = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global replication_coordinator, region_manager, health_monitor, client_router
    
    logger.info("🚀 Starting Cross-Region Replication System...")
    
    # Initialize components
    region_manager = RegionManager()
    await region_manager.initialize()
    
    replication_coordinator = ReplicationCoordinator(region_manager)
    await replication_coordinator.start()
    
    health_monitor = HealthMonitor(region_manager)
    await health_monitor.start_monitoring()
    
    client_router = ClientRouter(region_manager, health_monitor)
    
    # Store components in app state for access by routes
    app.state.replication_coordinator = replication_coordinator
    app.state.region_manager = region_manager
    app.state.health_monitor = health_monitor
    app.state.client_router = client_router
    
    logger.info("✅ All components initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down components...")
    await health_monitor.stop_monitoring()
    await replication_coordinator.stop()
    await region_manager.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Cross-Region Data Replication System",
    description="Geographic redundancy and disaster recovery for distributed log processing",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """System health check endpoint"""
    return {
        "status": "healthy",
        "regions": len(app.state.region_manager.regions) if hasattr(app.state, 'region_manager') and app.state.region_manager else 0,
        "replication_active": app.state.replication_coordinator.is_active() if hasattr(app.state, 'replication_coordinator') and app.state.replication_coordinator else False
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time replication status"""
    await websocket.accept()
    try:
        while True:
            if hasattr(app.state, 'health_monitor') and app.state.health_monitor:
                status = await app.state.health_monitor.get_comprehensive_status()
                await websocket.send_json(status)
            await asyncio.sleep(2)  # Update every 2 seconds
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Serve React frontend (must be last to avoid overriding other routes)
app.mount("/", StaticFiles(directory="../../frontend/build", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
