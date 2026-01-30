from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import json
import random
import sys
import os
from datetime import datetime

# Add backend directory to path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from api.routes import router
from analytics.traffic_analyzer import TrafficAnalyzer
from detectors.threat_detector import ThreatDetector

# Initialize components
traffic_analyzer = TrafficAnalyzer()
threat_detector = ThreatDetector()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Network Traffic Analysis System...")
    asyncio.create_task(generate_sample_traffic())
    asyncio.create_task(stream_analysis())
    yield
    # Shutdown (if needed)
    pass

app = FastAPI(title="Network Traffic Analysis System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set analyzer instances in routes
from api.routes import set_analyzers
set_analyzers(traffic_analyzer, threat_detector)

app.include_router(router, prefix="/api")

# WebSocket for real-time updates
active_connections = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except:
        active_connections.remove(websocket)

async def generate_sample_traffic():
    """Generate sample network traffic data for demo"""
    protocols = ["TCP", "UDP", "ICMP"]
    common_ports = [80, 443, 22, 53, 3306, 5432, 8080, 3389]
    
    while True:
        try:
            # Generate random connections
            for _ in range(random.randint(5, 15)):
                connection = {
                    "source_ip": f"192.168.1.{random.randint(1, 254)}",
                    "dest_ip": f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
                    "source_port": random.randint(1024, 65535),
                    "dest_port": random.choice(common_ports + [random.randint(1, 65535)]),
                    "protocol": random.choice(protocols),
                    "bytes": random.randint(100, 15000)
                }
                traffic_analyzer.add_connection(connection)
            
            await asyncio.sleep(1)  # Generate traffic every second
        except Exception as e:
            print(f"Traffic generation error: {e}")
            await asyncio.sleep(1)

async def stream_analysis():
    """Background task to analyze traffic and send updates"""
    while True:
        try:
            # Analyze recent traffic
            metrics = traffic_analyzer.get_current_metrics()
            threats = threat_detector.detect_threats(metrics)
            
            update = {
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "threats": threats
            }
            
            # Broadcast to all connected clients
            for connection in active_connections:
                try:
                    await connection.send_json(update)
                except:
                    pass
                    
        except Exception as e:
            print(f"Analysis error: {e}")
        
        await asyncio.sleep(2)

@app.get("/")
async def root():
    return {"status": "Network Traffic Analysis System Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
