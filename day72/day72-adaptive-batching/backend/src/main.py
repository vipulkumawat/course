"""
Day 72: Adaptive Batching System
Main application entry point
"""

import asyncio
import logging
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from adaptive_batching.adaptive_batcher import AdaptiveBatcher
from metrics.metrics_collector import MetricsCollector
from optimization.optimization_engine import OptimizationEngine
from monitoring.performance_monitor import PerformanceMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global components
adaptive_batcher = None
performance_monitor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global adaptive_batcher, performance_monitor
    
    print_status("Starting Adaptive Batching System...")
    
    # Initialize components
    metrics_collector = MetricsCollector()
    optimization_engine = OptimizationEngine()
    adaptive_batcher = AdaptiveBatcher(metrics_collector, optimization_engine)
    performance_monitor = PerformanceMonitor()
    
    # Start background tasks
    asyncio.create_task(adaptive_batcher.start())
    asyncio.create_task(performance_monitor.start())
    
    print_success("System initialized successfully")
    yield
    
    # Cleanup
    await adaptive_batcher.stop()
    await performance_monitor.stop()
    print_status("System shutdown complete")

# FastAPI app
app = FastAPI(title="Adaptive Batching System", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Adaptive Batching System is running"}

@app.get("/api/metrics")
async def get_metrics():
    """Get current system metrics"""
    if not adaptive_batcher:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return adaptive_batcher.get_current_metrics()

@app.get("/api/performance")
async def get_performance():
    """Get performance statistics"""
    if not performance_monitor:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return performance_monitor.get_performance_stats()

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await websocket.accept()
    
    try:
        while True:
            if adaptive_batcher:
                metrics = adaptive_batcher.get_current_metrics()
                performance = performance_monitor.get_performance_stats()
                
                data = {
                    "metrics": metrics,
                    "performance": performance,
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                await websocket.send_json(data)
            
            await asyncio.sleep(1)  # Send updates every second
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.post("/api/simulate-load")
async def simulate_load(load_config: dict):
    """Simulate different load patterns for testing"""
    if not adaptive_batcher:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    await adaptive_batcher.simulate_load(load_config)
    return {"status": "load simulation started"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# Helper functions for colored output
def print_status(message):
    print(f"\033[0;34m[INFO]\033[0m {message}")

def print_success(message):
    print(f"\033[0;32m[SUCCESS]\033[0m {message}")
