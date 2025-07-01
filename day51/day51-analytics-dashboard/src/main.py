import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from src.api.dashboard import router as dashboard_router
from src.websocket.manager import websocket_manager
from src.analytics.processor import AnalyticsProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include API routers
app.include_router(dashboard_router, prefix="/api")

# Initialize analytics processor
analytics = AnalyticsProcessor(settings.redis_url)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Initialize analytics processor
    await analytics.initialize()
    logger.info("Analytics processor initialized")
    
    # Start background tasks
    asyncio.create_task(periodic_metrics_broadcast())
    logger.info("Background tasks started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application")

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Serve the main dashboard page"""
    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "app_name": settings.app_name,
        "app_version": settings.app_version
    })

@app.get("/debug", response_class=HTMLResponse)
async def debug_page(request: Request):
    """Debug page to test functionality"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>Debug</title></head>
    <body>
        <h1>Dashboard Debug</h1>
        <p>✅ Page loaded</p>
        <button onclick="testAPI()">Test API</button>
        <div id="result"></div>
        <script>
            async function testAPI() {
                try {
                    const response = await fetch('/api/dashboard-stats');
                    const data = await response.json();
                    document.getElementById('result').innerHTML = '<p style="color:green">✅ API working: ' + JSON.stringify(data) + '</p>';
                } catch (error) {
                    document.getElementById('result').innerHTML = '<p style="color:red">❌ API error: ' + error.message + '</p>';
                }
            }
        </script>
    </body>
    </html>
    """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time updates"""
    client_id = await websocket_manager.connect(websocket)
    logger.info(f"WebSocket client {client_id} connected")
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await websocket_manager.handle_client_message(client_id, message)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from client {client_id}")
                await websocket_manager.send_personal_message({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                }, client_id)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        websocket_manager.disconnect(client_id)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.app_version,
        "connections": len(websocket_manager.active_connections)
    }

async def periodic_metrics_broadcast():
    """Broadcast periodic updates to connected clients"""
    while True:
        try:
            await asyncio.sleep(settings.refresh_interval / 1000)  # Convert ms to seconds
            
            # Get current stats
            stats = {
                'type': 'stats_update',
                'timestamp': datetime.now().isoformat(),
                'websocket_connections': len(websocket_manager.active_connections),
                'active_subscriptions': sum(
                    len(conn.subscriptions) 
                    for conn in websocket_manager.active_connections.values()
                )
            }
            
            # Broadcast to subscribers
            await websocket_manager.broadcast(stats, 'metrics')
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in periodic broadcast: {e}")
            await asyncio.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    ) 