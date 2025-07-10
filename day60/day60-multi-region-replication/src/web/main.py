from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio
import structlog
from datetime import datetime
import uuid

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
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="Day 60: Multi-Region Log Replication System",
    description="A distributed log replication system for high availability",
    version="1.0.0"
)

# In-memory storage for demo purposes
logs = []
connections = []

@app.get("/")
async def root():
    return {
        "message": "Day 60: Multi-Region Log Replication System",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "log_count": len(logs)
    }

@app.post("/logs")
async def add_log(log_data: dict):
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "region": log_data.get("region", "unknown"),
        "level": log_data.get("level", "info"),
        "message": log_data.get("message", ""),
        "metadata": log_data.get("metadata", {})
    }
    
    logs.append(log_entry)
    
    # Broadcast to all connected WebSocket clients
    await broadcast_log(log_entry)
    
    logger.info("Log entry added", log_id=log_entry["id"], region=log_entry["region"])
    
    return {"status": "success", "log_id": log_entry["id"]}

@app.get("/logs")
async def get_logs(region: str = None, limit: int = 100):
    filtered_logs = logs
    
    if region:
        filtered_logs = [log for log in logs if log.get("region") == region]
    
    return {
        "logs": filtered_logs[-limit:],
        "total": len(filtered_logs),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    
    logger.info("WebSocket client connected", client_count=len(connections))
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections.remove(websocket)
        logger.info("WebSocket client disconnected", client_count=len(connections))

async def broadcast_log(log_entry: dict):
    if connections:
        message = json.dumps({
            "type": "log_entry",
            "data": log_entry
        })
        
        for connection in connections:
            try:
                await connection.send_text(message)
            except:
                connections.remove(connection)

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
