from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import os
import psutil
import structlog
import asyncio
import json
import random
from datetime import datetime
from typing import List

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
    title="Log Profiler",
    description="A comprehensive log analysis and profiling system",
    version="1.0.0"
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main dashboard page with simulation capabilities"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Log Profiler Dashboard</title>
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #00b894 0%, #0984e3 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                overflow: hidden;
            }
            .header { 
                background: linear-gradient(135deg, #00b894 0%, #0984e3 100%);
                color: white;
                padding: 30px; 
                text-align: center;
            }
            .status { 
                color: #00b894; 
                font-weight: bold; 
                font-size: 18px;
            }
            .content {
                padding: 30px;
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .metric-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #00b894;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .metric-value {
                font-size: 24px;
                font-weight: bold;
                color: #00b894;
            }
            .metric-label {
                color: #666;
                margin-top: 5px;
            }
            .simulation-controls {
                background: #e8f5e8;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
            }
            .btn {
                background: linear-gradient(135deg, #00b894 0%, #0984e3 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                margin: 10px;
                transition: transform 0.2s;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .logs-container {
                background: #1e1e1e;
                color: #00ff00;
                padding: 20px;
                border-radius: 10px;
                height: 300px;
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                margin: 20px 0;
            }
            .log-entry {
                margin: 5px 0;
                padding: 5px;
                border-radius: 3px;
            }
            .log-info { color: #00ff00; }
            .log-warning { color: #ffff00; }
            .log-error { color: #ff0000; }
            .log-debug { color: #888888; }
            .progress-bar {
                width: 100%;
                height: 20px;
                background: #e0e0e0;
                border-radius: 10px;
                overflow: hidden;
                margin: 10px 0;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #00b894, #0984e3);
                transition: width 0.3s ease;
            }
            .endpoints {
                background: #f5f5f5;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .endpoints a {
                color: #00b894;
                text-decoration: none;
                margin: 0 10px;
            }
            .endpoints a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Log Profiler Dashboard</h1>
                <p class="status">✅ System is running</p>
                <p>Real-time log analysis and performance monitoring</p>
            </div>
            
            <div class="content">
                <div class="simulation-controls">
                    <h2>🎮 Simulation Controls</h2>
                    <p>Click the button below to simulate log processing and see real-time metrics</p>
                    <button class="btn" onclick="startSimulation()" id="simBtn">🚀 Start Log Processing Simulation</button>
                    <button class="btn" onclick="stopSimulation()" id="stopBtn" disabled>⏹️ Stop Simulation</button>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressBar" style="width: 0%"></div>
                    </div>
                    <p id="simStatus">Ready to start simulation</p>
                </div>

                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value" id="cpuMetric">--</div>
                        <div class="metric-label">CPU Usage (%)</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="memoryMetric">--</div>
                        <div class="metric-label">Memory Usage (%)</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="diskMetric">--</div>
                        <div class="metric-label">Disk Usage (%)</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="logCount">0</div>
                        <div class="metric-label">Logs Processed</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="errorRate">0%</div>
                        <div class="metric-label">Error Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="avgLatency">0ms</div>
                        <div class="metric-label">Avg Processing Time</div>
                    </div>
                </div>

                <div class="logs-container" id="logsContainer">
                    <div class="log-entry log-info">[INFO] Log Profiler Dashboard initialized</div>
                    <div class="log-entry log-info">[INFO] Ready to start log processing simulation</div>
                </div>

                <div class="endpoints">
                    <h3>🔗 Available Endpoints:</h3>
                    <a href="/docs" target="_blank">📚 API Documentation</a>
                    <a href="/health" target="_blank">❤️ Health Check</a>
                    <a href="/metrics" target="_blank">📊 System Metrics</a>
                    <a href="/ws" target="_blank">🔌 WebSocket</a>
                </div>
            </div>
        </div>

        <script>
            let ws = null;
            let simulationInterval = null;
            let logCount = 0;
            let errorCount = 0;
            let totalLatency = 0;

            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
                
                ws.onopen = function() {
                    addLog('WebSocket connected', 'info');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    updateMetrics(data);
                    addLog(data.message, data.level);
                };
                
                ws.onclose = function() {
                    addLog('WebSocket disconnected', 'warning');
                };
            }

            function updateMetrics(data) {
                if (data.type === 'metrics') {
                    document.getElementById('cpuMetric').textContent = data.cpu_percent.toFixed(1);
                    document.getElementById('memoryMetric').textContent = data.memory.percent.toFixed(1);
                    document.getElementById('diskMetric').textContent = data.disk.percent.toFixed(1);
                } else if (data.type === 'log_processed') {
                    logCount++;
                    document.getElementById('logCount').textContent = logCount;
                    
                    if (data.error) {
                        errorCount++;
                    }
                    
                    totalLatency += data.latency;
                    const avgLatency = totalLatency / logCount;
                    document.getElementById('avgLatency').textContent = avgLatency.toFixed(1) + 'ms';
                    
                    const errorRate = (errorCount / logCount * 100).toFixed(1);
                    document.getElementById('errorRate').textContent = errorRate + '%';
                }
            }

            function addLog(message, level) {
                const logsContainer = document.getElementById('logsContainer');
                const logEntry = document.createElement('div');
                logEntry.className = `log-entry log-${level}`;
                logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
                logsContainer.appendChild(logEntry);
                logsContainer.scrollTop = logsContainer.scrollHeight;
                
                // Keep only last 50 log entries
                while (logsContainer.children.length > 50) {
                    logsContainer.removeChild(logsContainer.firstChild);
                }
            }

            function startSimulation() {
                document.getElementById('simBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('simStatus').textContent = 'Simulation running...';
                
                // Reset counters
                logCount = 0;
                errorCount = 0;
                totalLatency = 0;
                
                // Start progress bar animation
                let progress = 0;
                const progressBar = document.getElementById('progressBar');
                
                simulationInterval = setInterval(() => {
                    progress += Math.random() * 2;
                    if (progress > 100) progress = 100;
                    progressBar.style.width = progress + '%';
                    
                    if (progress >= 100) {
                        stopSimulation();
                    }
                }, 100);
                
                addLog('Log processing simulation started', 'info');
            }

            function stopSimulation() {
                document.getElementById('simBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('simStatus').textContent = 'Simulation stopped';
                document.getElementById('progressBar').style.width = '0%';
                
                if (simulationInterval) {
                    clearInterval(simulationInterval);
                    simulationInterval = null;
                }
                
                addLog('Log processing simulation stopped', 'info');
            }

            // Connect WebSocket on page load
            connectWebSocket();
            
            // Update metrics every 2 seconds
            setInterval(async () => {
                try {
                    const response = await fetch('/metrics');
                    const data = await response.json();
                    updateMetrics({type: 'metrics', ...data});
                } catch (error) {
                    console.error('Failed to fetch metrics:', error);
                }
            }, 2000);
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "log-profiler"
    }

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get metrics")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(2)
            
            # Simulate log processing metrics
            metrics = await get_metrics()
            await websocket.send_text(json.dumps({
                "type": "metrics",
                "message": f"System metrics updated - CPU: {metrics['cpu_percent']:.1f}%, Memory: {metrics['memory']['percent']:.1f}%",
                "level": "info",
                **metrics
            }))
            
            # Simulate log processing events
            if random.random() < 0.3:  # 30% chance of log event
                latency = random.uniform(10, 100)
                error = random.random() < 0.05  # 5% error rate
                
                await websocket.send_text(json.dumps({
                    "type": "log_processed",
                    "message": f"Log entry processed in {latency:.1f}ms" + (" (ERROR)" if error else ""),
                    "level": "error" if error else "info",
                    "latency": latency,
                    "error": error
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Log Profiler application starting up")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Log Profiler application shutting down")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
