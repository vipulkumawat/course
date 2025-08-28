import asyncio
import json
from datetime import datetime
from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, List

from ..health.collector import HealthCollector, HealthStatus
from ..alerts.manager import AlertManager, Alert
from config.development.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
health_collector = None
alert_manager = None
websocket_connections: List[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    global health_collector, alert_manager
    
    # Startup
    logger.info("Starting Health Monitoring System...")
    
    health_collector = HealthCollector(settings)
    alert_manager = AlertManager(settings)
    
    # Register some demo components
    health_collector.register_component(
        "log-collector-1", 
        "Log Collector Service",
        "http://localhost:8001/health"
    )
    
    health_collector.register_component(
        "message-queue-1",
        "Message Queue Service", 
        "http://localhost:8002/health"
    )
    
    health_collector.register_component(
        "processing-engine-1",
        "Log Processing Engine",
        "http://localhost:8003/health"
    )
    
    # Start services
    await alert_manager.start()
    
    # Start health collection in background
    asyncio.create_task(health_collector.start())
    
    # Start alert evaluation loop
    asyncio.create_task(alert_evaluation_loop())
    
    # Start WebSocket broadcast loop
    asyncio.create_task(websocket_broadcast_loop())
    
    logger.info("Health Monitoring System started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Health Monitoring System...")
    await health_collector.stop()
    await alert_manager.stop()

app = FastAPI(
    title="Health Monitoring System",
    description="Comprehensive health monitoring for distributed log platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def alert_evaluation_loop():
    """Background task to evaluate alerts"""
    while True:
        try:
            if health_collector and alert_manager:
                latest_metrics = (
                    health_collector.system_metrics[-1] 
                    if health_collector.system_metrics else None
                )
                
                await alert_manager.evaluate_metrics(
                    latest_metrics,
                    health_collector.component_health
                )
                
        except Exception as e:
            logger.error(f"Error in alert evaluation: {e}")
            
        await asyncio.sleep(settings.alert_check_interval)

async def websocket_broadcast_loop():
    """Background task to broadcast updates via WebSocket"""
    logger.info("WebSocket broadcast loop started")
    while True:
        try:
            logger.debug(f"WebSocket broadcast loop iteration - connections: {len(websocket_connections)}")
            if websocket_connections and health_collector and alert_manager:
                health_data = health_collector.get_health_summary()
                alert_data = alert_manager.get_alert_summary()
                
                message = {
                    "type": "health_update",
                    "timestamp": datetime.now().isoformat(),
                    "health": health_data,
                    "alerts": alert_data
                }
                
                logger.info(f"Broadcasting health update to {len(websocket_connections)} clients")
                
                # Broadcast to all connected clients
                disconnected = []
                for websocket in websocket_connections:
                    try:
                        await websocket.send_text(json.dumps(message))
                        logger.debug("Message sent successfully to WebSocket client")
                    except Exception as e:
                        logger.error(f"Failed to send message to WebSocket client: {e}")
                        disconnected.append(websocket)
                        
                # Remove disconnected clients
                for ws in disconnected:
                    websocket_connections.remove(ws)
                    logger.info(f"Removed disconnected WebSocket client. Total: {len(websocket_connections)}")
                    
            else:
                logger.debug("Skipping broadcast - no connections or services not ready")
                
        except Exception as e:
            logger.error(f"Error in WebSocket broadcast: {e}")
            
        await asyncio.sleep(5)  # Broadcast every 5 seconds

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(websocket_connections)}")
    
    try:
        # Keep connection alive by waiting for disconnect
        while True:
            # Wait for any message or disconnect
            try:
                await websocket.receive_text()
            except:
                # Client disconnected or connection error
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(websocket_connections)}")

@app.get("/")
async def read_root():
    return {"message": "Health Monitoring System API", "version": "1.0.0"}

@app.get("/health")
async def get_system_health():
    """Get overall system health status"""
    if not health_collector:
        raise HTTPException(status_code=503, detail="Health collector not initialized")
        
    return health_collector.get_health_summary()

@app.get("/health/components")
async def get_component_health():
    """Get detailed component health information"""
    if not health_collector:
        raise HTTPException(status_code=503, detail="Health collector not initialized")
        
    return {
        "components": health_collector.component_health,
        "registered_count": len(health_collector.registered_components)
    }

@app.get("/health/metrics")
async def get_system_metrics():
    """Get system metrics history"""
    if not health_collector:
        raise HTTPException(status_code=503, detail="Health collector not initialized")
        
    # Return last 100 metrics
    recent_metrics = health_collector.system_metrics[-100:]
    
    return {
        "metrics": [
            {
                "timestamp": m.timestamp.isoformat(),
                "cpu_percent": m.cpu_percent,
                "memory_percent": m.memory_percent,
                "disk_percent": m.disk_percent,
                "process_count": m.process_count,
                "load_average": m.load_average
            }
            for m in recent_metrics
        ]
    }

@app.get("/alerts")
async def get_alerts():
    """Get current alerts and alert summary"""
    if not alert_manager:
        raise HTTPException(status_code=503, detail="Alert manager not initialized")
        
    return alert_manager.get_alert_summary()

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge a specific alert"""
    if not alert_manager:
        raise HTTPException(status_code=503, detail="Alert manager not initialized")
        
    success = alert_manager.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    return {"status": "acknowledged", "alert_id": alert_id}

@app.post("/components/register")
async def register_component(component_data: dict):
    """Register a new component for monitoring"""
    if not health_collector:
        raise HTTPException(status_code=503, detail="Health collector not initialized")
        
    required_fields = ["component_id", "name", "health_endpoint"]
    if not all(field in component_data for field in required_fields):
        raise HTTPException(
            status_code=400, 
            detail="Missing required fields: component_id, name, health_endpoint"
        )
        
    health_collector.register_component(
        component_data["component_id"],
        component_data["name"],
        component_data["health_endpoint"],
        component_data.get("metadata", {})
    )
    
    return {"status": "registered", "component_id": component_data["component_id"]}

@app.get("/dashboard")
async def dashboard():
    """Serve the dashboard HTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Health Monitoring Dashboard</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .status { padding: 8px 16px; border-radius: 20px; color: white; font-weight: bold; }
            .healthy { background: #10b981; }
            .warning { background: #f59e0b; }
            .critical { background: #ef4444; }
            .unknown { background: #6b7280; }
            .metric { display: flex; justify-content: space-between; margin: 10px 0; }
            .progress { background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden; }
            .progress-bar { height: 100%; transition: width 0.3s; }
            .progress-normal { background: #10b981; }
            .progress-warning { background: #f59e0b; }
            .progress-critical { background: #ef4444; }
            #connectionStatus { position: fixed; top: 10px; right: 10px; padding: 10px; border-radius: 4px; }
            .connected { background: #10b981; color: white; }
            .disconnected { background: #ef4440; color: white; }
        </style>
    </head>
    <body>
        <div id="connectionStatus" class="disconnected">Disconnected</div>
        
        <div class="header">
            <h1>🏥 Health Monitoring Dashboard</h1>
            <p>Real-time monitoring of distributed log platform components</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Overall System Health</h3>
                <div id="overallStatus" class="status unknown">Unknown</div>
                <div id="lastUpdate">Last Update: Never</div>
            </div>
            
            <div class="card">
                <h3>System Metrics</h3>
                <div id="systemMetrics">
                    <div class="metric">
                        <span>CPU Usage:</span>
                        <span id="cpuUsage">--%</span>
                    </div>
                    <div class="progress">
                        <div id="cpuProgress" class="progress-bar progress-normal" style="width: 0%"></div>
                    </div>
                    
                    <div class="metric">
                        <span>Memory Usage:</span>
                        <span id="memoryUsage">--%</span>
                    </div>
                    <div class="progress">
                        <div id="memoryProgress" class="progress-bar progress-normal" style="width: 0%"></div>
                    </div>
                    
                    <div class="metric">
                        <span>Disk Usage:</span>
                        <span id="diskUsage">--%</span>
                    </div>
                    <div class="progress">
                        <div id="diskProgress" class="progress-bar progress-normal" style="width: 0%"></div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>Component Status</h3>
                <div id="componentStatus">No components registered</div>
            </div>
            
            <div class="card">
                <h3>Active Alerts</h3>
                <div id="activeAlerts">No active alerts</div>
            </div>
        </div>
        
        <script>
            let ws;
            let reconnectInterval;
            
            function connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = protocol + '//' + window.location.host + '/ws';
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function(event) {
                    console.log('WebSocket connected');
                    document.getElementById('connectionStatus').textContent = 'Connected';
                    document.getElementById('connectionStatus').className = 'connected';
                    clearInterval(reconnectInterval);
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.type === 'health_update') {
                        updateDashboard(data);
                    }
                };
                
                ws.onclose = function(event) {
                    console.log('WebSocket disconnected');
                    document.getElementById('connectionStatus').textContent = 'Disconnected';
                    document.getElementById('connectionStatus').className = 'disconnected';
                    
                    // Attempt to reconnect every 5 seconds
                    reconnectInterval = setInterval(connect, 5000);
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }
            
            function updateDashboard(data) {
                const health = data.health;
                const alerts = data.alerts;
                
                // Update overall status
                const statusElement = document.getElementById('overallStatus');
                statusElement.textContent = health.overall_status.toUpperCase();
                statusElement.className = 'status ' + health.overall_status;
                
                // Update last update time
                document.getElementById('lastUpdate').textContent = 
                    'Last Update: ' + new Date(data.timestamp).toLocaleTimeString();
                
                // Update system metrics
                if (health.system_metrics) {
                    const metrics = health.system_metrics;
                    
                    updateMetric('cpu', metrics.cpu_percent);
                    updateMetric('memory', metrics.memory_percent);
                    updateMetric('disk', metrics.disk_percent);
                }
                
                // Update component status
                updateComponentStatus(health.components);
                
                // Update alerts
                updateAlerts(alerts);
            }
            
            function updateMetric(type, value) {
                const usageElement = document.getElementById(type + 'Usage');
                const progressElement = document.getElementById(type + 'Progress');
                
                usageElement.textContent = value.toFixed(1) + '%';
                progressElement.style.width = value + '%';
                
                // Update color based on thresholds
                let colorClass = 'progress-normal';
                if (value > 90) {
                    colorClass = 'progress-critical';
                } else if (value > 70) {
                    colorClass = 'progress-warning';
                }
                
                progressElement.className = 'progress-bar ' + colorClass;
            }
            
            function updateComponentStatus(components) {
                const container = document.getElementById('componentStatus');
                
                if (!components || Object.keys(components).length === 0) {
                    container.innerHTML = 'No components registered';
                    return;
                }
                
                let html = '';
                for (const [id, component] of Object.entries(components)) {
                    html += '<div class="metric">';
                    html += '<span>' + component.name + ':</span>';
                    html += '<span class="status ' + component.status + '">' + 
                           component.status.toUpperCase() + '</span>';
                    html += '</div>';
                }
                
                container.innerHTML = html;
            }
            
            function updateAlerts(alerts) {
                const container = document.getElementById('activeAlerts');
                
                if (alerts.active_alerts === 0) {
                    container.innerHTML = 'No active alerts';
                    return;
                }
                
                let html = '<div>Active: ' + alerts.active_alerts + 
                          ' | Critical: ' + alerts.critical_alerts + '</div>';
                
                if (alerts.active_alert_list && alerts.active_alert_list.length > 0) {
                    alerts.active_alert_list.forEach(alert => {
                        html += '<div style="margin: 5px 0; padding: 5px; border-left: 3px solid ';
                        html += alert.severity === 'critical' ? '#ef4444' : '#f59e0b';
                        html += '; background: #f9fafb;">';
                        html += '<strong>' + alert.title + '</strong><br>';
                        html += '<small>' + alert.description + '</small>';
                        html += '</div>';
                    });
                }
                
                container.innerHTML = html;
            }
            
            // Connect on page load
            connect();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )
