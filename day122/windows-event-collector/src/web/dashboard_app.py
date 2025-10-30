"""Windows Event Log Agent Web Dashboard"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from prometheus_client.asgi import make_asgi_app

from config.agent_config import config

logger = logging.getLogger(__name__)

# Global agent reference
active_agent = None

app = FastAPI(title="Windows Event Log Agent Dashboard", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
# Expose Prometheus metrics at /metrics as well (in addition to standalone server)
app.mount("/metrics", make_asgi_app())
templates = Jinja2Templates(directory="src/web/templates")

# WebSocket connections for real-time updates
active_connections = []

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "agent_config": config.dict()
    })

@app.get("/api/status")
async def get_agent_status():
    """Get current agent status"""
    global active_agent
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'running': active_agent.is_running if active_agent else False,
        'channels': len(config.channels),
        'stats': active_agent.get_stats() if active_agent else {},
        'config': {
            'channels': config.channels,
            'batch_size': config.max_events_per_batch,
            'batch_timeout': config.batch_timeout_seconds
        }
    }
    
    return JSONResponse(status)

@app.get("/api/events/recent")
async def get_recent_events():
    """Get recently collected events"""
    # In a real implementation, this would read from a circular buffer
    # For now, return mock data
    recent_events = [
        {
            'timestamp': datetime.now().isoformat(),
            'channel': 'System',
            'event_id': 1001,
            'level': 'Information',
            'source': 'Service Control Manager',
            'message': 'Service started successfully'
        },
        {
            'timestamp': datetime.now().isoformat(),
            'channel': 'Application',
            'event_id': 1000,
            'level': 'Warning',
            'source': 'Application',
            'message': 'Application warning message'
        }
    ]
    
    return JSONResponse(recent_events)

@app.get("/api/channels")
async def get_channel_info():
    """Get information about configured channels"""
    channel_info = {}
    
    for channel in config.channels:
        channel_info[channel] = {
            'name': channel,
            'enabled': True,
            'events_collected': 0,  # Would be tracked in real implementation
            'last_event': None,
            'status': 'active'
        }
    
    return JSONResponse(channel_info)

@app.post("/api/control/start")
async def start_agent():
    """Start the event collection agent"""
    global active_agent
    
    try:
        if active_agent and active_agent.is_running:
            return JSONResponse({'status': 'already_running'})
            
        # This would typically start the agent
        # For demo purposes, we'll simulate it
        return JSONResponse({'status': 'started', 'message': 'Event collection started'})
        
    except Exception as e:
        logger.error(f"Error starting agent: {e}")
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@app.post("/api/control/stop")
async def stop_agent():
    """Stop the event collection agent"""
    global active_agent
    
    try:
        if active_agent:
            await active_agent.stop_collection()
            
        return JSONResponse({'status': 'stopped', 'message': 'Event collection stopped'})
        
    except Exception as e:
        logger.error(f"Error stopping agent: {e}")
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            
            if active_agent:
                stats = active_agent.get_stats()
                await websocket.send_text(json.dumps({
                    'type': 'stats_update',
                    'data': stats,
                    'timestamp': datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_event(event_data: Dict):
    """Broadcast event to all connected WebSocket clients"""
    message = json.dumps({
        'type': 'new_event',
        'data': event_data,
        'timestamp': datetime.now().isoformat()
    })
    
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except:
            disconnected.append(connection)
            
    # Remove disconnected clients
    for conn in disconnected:
        active_connections.remove(conn)

def set_active_agent(agent):
    """Set the active agent for dashboard monitoring"""
    global active_agent
    active_agent = agent

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
