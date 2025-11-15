from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import asyncio
import json
import time
from typing import Dict, Any, List
import redis.asyncio as redis
import structlog
import yaml
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from collectors.system_metrics import SystemMetricsCollector
from collectors.app_metrics import AppMetricsCollector
from correlation.engine import CorrelationEngine

logger = structlog.get_logger()

# Load configuration
# Get project root (two levels up from this file: src/api/server.py -> src -> project root)
project_root = Path(__file__).parent.parent.parent
config_path = project_root / "config" / "apm_config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

app = FastAPI(title="APM Integration API", version="1.0.0")

# Middleware to track all requests
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics/current":
            return await call_next(request)
        
        start_time = time.time()
        response = await call_next(request)
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Record metrics if app_collector is initialized
        if app_collector:
            is_error = response.status_code >= 400
            await app_collector.record_request(response_time, is_error=is_error)
        
        return response

# Add middleware (order matters - metrics should be after CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(MetricsMiddleware)

# Global components
redis_client = None
system_collector = None
app_collector = None
correlation_engine = None
websocket_connections = []

@app.on_event("startup")
async def startup_event():
    global redis_client, system_collector, app_collector, correlation_engine
    
    # Initialize Redis connection
    redis_client = redis.Redis.from_url(config['apm']['storage']['redis_url'])
    
    # Initialize collectors
    system_collector = SystemMetricsCollector(redis_client, config['apm']['metrics']['collection_interval'])
    app_collector = AppMetricsCollector(redis_client)
    correlation_engine = CorrelationEngine(redis_client, config['apm'])
    
    # Start system metrics collection
    asyncio.create_task(system_collector.start_collection())
    
    logger.info("APM Integration API started successfully")

@app.on_event("shutdown") 
async def shutdown_event():
    if system_collector:
        system_collector.stop()
    if redis_client:
        await redis_client.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/logs")
async def process_log(log_data: Dict[str, Any]):
    """Process and enrich a log entry"""
    try:
        enriched_log = await correlation_engine.process_log_entry(log_data)
        
        # Broadcast to WebSocket clients
        await broadcast_log_update(enriched_log)
        
        return {
            "status": "processed",
            "correlation_id": enriched_log.correlation_id,
            "enhancement_level": enriched_log.enhancement_level
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/current")
async def get_current_metrics():
    """Get current system and application metrics"""
    # Get latest system metrics by searching for the most recent metrics key
    # Metrics are collected every 5 seconds, so look back up to 10 seconds
    current_time = int(time.time())
    system_data = {}
    metrics_timestamp = current_time
    
    # Search for the most recent metrics (look back up to 10 seconds)
    for i in range(10):
        system_key = f"metrics:{current_time - i}"
        data = await redis_client.hgetall(system_key)
        if data:
            system_data = data
            metrics_timestamp = current_time - i
            break
    
    # Get application metrics
    app_metrics = await app_collector.get_current_metrics()
    
    return {
        "system": {k.decode(): float(v) for k, v in system_data.items() if k.decode() != 'timestamp'} if system_data else {},
        "application": {
            "request_count": app_metrics.request_count,
            "error_count": app_metrics.error_count,
            "avg_response_time": app_metrics.response_time_avg,
            "p95_response_time": app_metrics.response_time_p95,
            "active_connections": app_metrics.active_connections
        },
        "timestamp": metrics_timestamp
    }

@app.get("/logs/recent")
async def get_recent_logs(hours: int = 1):
    """Get recent enriched logs"""
    logs = await correlation_engine.get_recent_logs(hours)
    return [log.__dict__ for log in logs]

@app.get("/alerts/recent")
async def get_recent_alerts():
    """Get recent alerts"""
    current_time = int(time.time())
    alerts = []
    
    # Get all alert keys from the last hour
    # Use SCAN to find all alert keys, then filter by timestamp
    alert_keys = []
    cursor = 0
    while True:
        cursor, keys = await redis_client.scan(cursor, match="alerts:*", count=100)
        for key in keys:
            # Extract timestamp from key (format: alerts:timestamp)
            try:
                key_str = key.decode() if isinstance(key, bytes) else key
                timestamp_str = key_str.split(':')[1]
                timestamp = int(timestamp_str)
                # Only include alerts from the last hour
                if current_time - timestamp <= 3600:
                    alert_keys.append((key_str, timestamp))
            except (ValueError, IndexError):
                continue
        if cursor == 0:
            break
    
    # Get alert data
    for key_str, timestamp in alert_keys:
        data = await redis_client.get(key_str)
        if data:
            try:
                alert_data = json.loads(data)
                # Ensure timestamp is in the alert data
                if 'timestamp' not in alert_data:
                    alert_data['timestamp'] = timestamp
                alerts.append(alert_data)
            except json.JSONDecodeError:
                continue
    
    return sorted(alerts, key=lambda x: x.get('timestamp', 0), reverse=True)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            metrics = await get_current_metrics()
            await websocket.send_json({
                "type": "metrics_update",
                "data": metrics
            })
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)

async def broadcast_log_update(enriched_log):
    """Broadcast log update to all WebSocket connections"""
    message = {
        "type": "log_update", 
        "data": enriched_log.__dict__
    }
    
    for websocket in websocket_connections[:]:  # Copy list to avoid modification during iteration
        try:
            await websocket.send_json(message)
        except:
            websocket_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
