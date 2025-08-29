from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
from typing import List
from src.scaling.scaling_coordinator import ScalingCoordinator

app = FastAPI(title="Automated Scaling Dashboard", version="1.0.0")

# Global scaling coordinator instance
scaling_coordinator = None
connected_websockets: List[WebSocket] = []
background_tasks = []

@app.on_event("startup")
async def startup_event():
    global scaling_coordinator
    scaling_coordinator = ScalingCoordinator("config/scaling_config.yaml")
    await scaling_coordinator.initialize()
    
    # Start scaling loop
    scaling_task = asyncio.create_task(scaling_coordinator.start_scaling_loop())
    background_tasks.append(scaling_task)
    
    # Start status broadcast
    broadcast_task = asyncio.create_task(broadcast_status())
    background_tasks.append(broadcast_task)

@app.on_event("shutdown")
async def shutdown_event():
    global scaling_coordinator, background_tasks
    
    logging.info("Shutting down automated scaling system...")
    
    # Cancel all background tasks
    for task in background_tasks:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    # Stop the scaling coordinator
    if scaling_coordinator:
        scaling_coordinator.stop()
    
    # Close all websocket connections
    for websocket in connected_websockets:
        try:
            await websocket.close()
        except:
            pass
    
    connected_websockets.clear()
    background_tasks.clear()
    
    logging.info("Automated scaling system shutdown complete")

@app.get("/")
async def read_root():
    return {"message": "Automated Scaling System API", "status": "running"}

@app.get("/api/status")
async def get_status():
    """Get current scaling system status"""
    if scaling_coordinator:
        return scaling_coordinator.get_status()
    return {"error": "Scaling coordinator not initialized"}

@app.get("/api/metrics")
async def get_metrics():
    """Get current metrics for all components"""
    if scaling_coordinator:
        metrics = scaling_coordinator.metrics_collector.get_latest_metrics()
        return {
            component_id: {
                "cpu_percent": m.cpu_percent,
                "memory_percent": m.memory_percent,
                "queue_depth": m.queue_depth,
                "response_time_ms": m.response_time_ms,
                "throughput_per_sec": m.throughput_per_sec,
                "instance_count": m.instance_count,
                "timestamp": m.timestamp
            }
            for component_id, m in metrics.items()
        }
    return {}

@app.get("/api/scaling-history")
async def get_scaling_history():
    """Get recent scaling actions"""
    if scaling_coordinator:
        history = scaling_coordinator.policy_engine.scaling_history[-20:]
        return [
            {
                "component_id": h.component_id,
                "action": h.action.value,
                "target_instances": h.target_instances,
                "current_instances": h.current_instances,
                "reason": h.reason,
                "timestamp": h.timestamp
            }
            for h in history
        ]
    return []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)

async def broadcast_status():
    """Broadcast status updates to all connected websockets"""
    try:
        while True:
            if connected_websockets and scaling_coordinator:
                status = scaling_coordinator.get_status()
                metrics = scaling_coordinator.metrics_collector.get_latest_metrics()
                
                broadcast_data = {
                    "type": "status_update",
                    "status": status,
                    "metrics": {
                        component_id: {
                            "cpu_percent": m.cpu_percent,
                            "queue_depth": m.queue_depth,
                            "instance_count": m.instance_count
                        }
                        for component_id, m in metrics.items()
                    }
                }
                
                # Send to all connected clients
                disconnected = []
                for websocket in connected_websockets:
                    try:
                        await websocket.send_text(json.dumps(broadcast_data))
                    except:
                        disconnected.append(websocket)
                
                # Remove disconnected websockets
                for ws in disconnected:
                    if ws in connected_websockets:
                        connected_websockets.remove(ws)
            
            await asyncio.sleep(5)  # Broadcast every 5 seconds
    except asyncio.CancelledError:
        logging.info("Status broadcast cancelled, shutting down...")
    except Exception as e:
        logging.error(f"Error in status broadcast: {e}")
    finally:
        logging.info("Status broadcast stopped")

# Mount static files for React app
app.mount("/static", StaticFiles(directory="web/build/static"), name="static")

@app.get("/{path:path}")
async def serve_react_app(path: str):
    """Serve React application for all routes"""
    try:
        with open("web/build/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return {"error": "React app not built. Run 'npm run build' in web directory."}
