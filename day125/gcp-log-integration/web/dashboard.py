"""Real-time GCP Log Ingestion Dashboard"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import List
import os
import time

app = FastAPI(title="GCP Log Integration Dashboard")

# Store active WebSocket connections
active_connections: List[WebSocket] = []

# Get the base directory (where dashboard.py is located)
BASE_DIR = Path(__file__).parent.parent
STATS_FILE = BASE_DIR / "checkpoints" / "stats.json"

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GCP Log Integration Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            min-height: 100vh;
            padding: 20px;
            color: #f1f5f9;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        .header h1 {
            font-size: 32px;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 500;
            color: #10b981;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #10b981;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .last-update {
            font-size: 13px;
            color: #94a3b8;
            margin-top: 8px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(10px);
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.4);
            border-color: rgba(148, 163, 184, 0.2);
        }
        
        .metric-card.total {
            border-top: 4px solid #14b8a6;
        }
        
        .metric-card.error {
            border-top: 4px solid #f59e0b;
        }
        
        .metric-card.success {
            border-top: 4px solid #10b981;
        }
        
        .metric-label {
            font-size: 13px;
            font-weight: 600;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        
        .metric-value {
            font-size: 36px;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 4px;
        }
        
        .metric-subtitle {
            font-size: 14px;
            color: #cbd5e1;
        }
        
        .projects-section {
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        .projects-section h2 {
            font-size: 24px;
            font-weight: 600;
            color: #f1f5f9;
            margin-bottom: 20px;
        }
        
        .project-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .project-card {
            background: rgba(15, 23, 42, 0.6);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #14b8a6;
            transition: all 0.2s;
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        .project-card:hover {
            background: rgba(15, 23, 42, 0.8);
            transform: translateX(4px);
            border-color: rgba(148, 163, 184, 0.2);
        }
        
        .project-name {
            font-size: 18px;
            font-weight: 600;
            color: #f1f5f9;
            margin-bottom: 12px;
        }
        
        .project-stats {
            display: flex;
            gap: 20px;
            margin-top: 12px;
        }
        
        .stat-item {
            flex: 1;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #f1f5f9;
        }
        
        .stat-label {
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .error-count {
            color: #f59e0b;
        }
        
        .success-count {
            color: #10b981;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #94a3b8;
        }
        
        .empty-state h3 {
            font-size: 20px;
            margin-bottom: 10px;
            color: #cbd5e1;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span>🌐</span>
                GCP Log Integration Dashboard
            </h1>
            <div class="status-indicator">
                <span class="status-dot"></span>
                <span>Real-time Updates Active</span>
            </div>
            <div class="last-update" id="lastUpdate">Last updated: --</div>
        </div>
        
        <div class="metrics-grid" id="totalMetrics"></div>
        
        <div class="projects-section">
            <h2>Project Metrics</h2>
            <div id="projectMetrics" class="project-grid"></div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;
        
        function formatNumber(num) {
            return new Intl.NumberFormat('en-US').format(num);
        }
        
        function updateLastUpdate() {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit', 
                second: '2-digit' 
            });
            document.getElementById('lastUpdate').textContent = `Last updated: ${timeStr}`;
        }
        
        function renderMetrics(data) {
            const totalMetrics = document.getElementById('totalMetrics');
            const projectMetrics = document.getElementById('projectMetrics');
            
            if (!totalMetrics || !projectMetrics) return;
            
            // Render total metrics
            totalMetrics.innerHTML = `
                <div class="metric-card total">
                    <div class="metric-label">Total Logs Ingested</div>
                    <div class="metric-value">${formatNumber(data.total_ingested || 0)}</div>
                    <div class="metric-subtitle">All projects combined</div>
                </div>
                <div class="metric-card error">
                    <div class="metric-label">Total Errors</div>
                    <div class="metric-value error-count">${formatNumber(data.total_errors || 0)}</div>
                    <div class="metric-subtitle">Errors across all projects</div>
                </div>
                <div class="metric-card success">
                    <div class="metric-label">Success Rate</div>
                    <div class="metric-value success-count">
                        ${data.total_ingested > 0 
                            ? ((100 * (data.total_ingested - data.total_errors) / data.total_ingested).toFixed(1))
                            : '0.0'}%
                    </div>
                    <div class="metric-subtitle">Successful ingestion rate</div>
                </div>
            `;
            
            // Render project metrics
            const projects = data.by_project || {};
            if (Object.keys(projects).length === 0) {
                projectMetrics.innerHTML = `
                    <div class="empty-state">
                        <h3>No project data available</h3>
                        <p>Waiting for log ingestion to start...</p>
                    </div>
                `;
            } else {
                projectMetrics.innerHTML = Object.entries(projects).map(([proj, stats]) => `
                    <div class="project-card">
                        <div class="project-name">${proj}</div>
                        <div class="project-stats">
                            <div class="stat-item">
                                <div class="stat-value success-count">${formatNumber(stats.ingested || 0)}</div>
                                <div class="stat-label">Ingested</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value error-count">${formatNumber(stats.errors || 0)}</div>
                                <div class="stat-label">Errors</div>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
            
            updateLastUpdate();
        }
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                console.log('WebSocket connected');
                reconnectAttempts = 0;
                document.querySelector('.status-indicator').innerHTML = `
                    <span class="status-dot"></span>
                    <span>Real-time Updates Active</span>
                `;
            };
            
            ws.onmessage = (event) => {
                try {
                    // Handle ping/pong messages
                    if (event.data === 'ping') {
                        ws.send('pong');
                        return;
                    }
                    if (event.data === 'pong') {
                        return;
                    }
                    
                    // Handle JSON metrics data
                    const data = JSON.parse(event.data);
                    console.log('Received metrics update:', data);
                    renderMetrics(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error, event.data);
                }
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            ws.onclose = () => {
                console.log('WebSocket disconnected');
                document.querySelector('.status-indicator').innerHTML = `
                    <span class="status-dot" style="background: #f59e0b;"></span>
                    <span>Connection Lost - Reconnecting...</span>
                `;
                
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    setTimeout(connectWebSocket, 2000 * reconnectAttempts);
                } else {
                    document.querySelector('.status-indicator').innerHTML = `
                        <span class="status-dot" style="background: #f59e0b;"></span>
                        <span>Connection Failed - Using Polling</span>
                    `;
                    // Fallback to polling
                    startPolling();
                }
            };
        }
        
        function startPolling() {
            async function fetchMetrics() {
                try {
                    const response = await fetch('/metrics/gcp');
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const data = await response.json();
                    renderMetrics(data);
                } catch (error) {
                    console.error('Error fetching metrics:', error);
                }
            }
            
            fetchMetrics();
            setInterval(fetchMetrics, 5000);
        }
        
        // Initialize
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                connectWebSocket();
                // Initial fetch in case WebSocket takes time
                fetch('/metrics/gcp')
                    .then(r => r.json())
                    .then(renderMetrics)
                    .catch(err => console.error('Initial fetch error:', err));
            });
        } else {
            connectWebSocket();
            fetch('/metrics/gcp')
                .then(r => r.json())
                .then(renderMetrics)
                .catch(err => console.error('Initial fetch error:', err));
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def dashboard():
    return HTMLResponse(html_content)

def get_metrics():
    """Read metrics from stats file"""
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading stats: {e}")
            return _get_default_metrics()
    return _get_default_metrics()

@app.get("/metrics/gcp")
async def get_metrics_endpoint():
    """HTTP endpoint for metrics"""
    return get_metrics()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics updates"""
    await websocket.accept()
    active_connections.append(websocket)
    print(f"WebSocket connected. Total connections: {len(active_connections)}")
    try:
        # Send initial metrics
        metrics = get_metrics()
        await websocket.send_json(metrics)
        
        # Keep connection alive and listen for disconnects
        while True:
            try:
                # Wait for any message from client (ping/pong)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo back or handle ping
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_text("ping")
                except:
                    break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        print(f"WebSocket removed. Total connections: {len(active_connections)}")

async def broadcast_metrics():
    """Background task to broadcast metrics to all connected WebSocket clients"""
    last_modified = 0
    last_broadcast = 0
    while True:
        try:
            if active_connections:
                # Check if file has been modified
                current_modified = 0
                if STATS_FILE.exists():
                    current_modified = os.path.getmtime(STATS_FILE)
                
                current_time = time.time()
                
                # Broadcast if file changed OR every 3 seconds (whichever comes first)
                should_broadcast = (
                    current_modified != last_modified or 
                    (current_time - last_broadcast) >= 3.0
                )
                
                if should_broadcast:
                    metrics = get_metrics()
                    last_modified = current_modified
                    last_broadcast = current_time
                    
                    # Send to all connected clients
                    disconnected = []
                    for connection in active_connections:
                        try:
                            await connection.send_json(metrics)
                        except Exception as e:
                            print(f"Error sending to client: {e}")
                            disconnected.append(connection)
                    
                    # Remove disconnected clients
                    for conn in disconnected:
                        if conn in active_connections:
                            active_connections.remove(conn)
                    
                    if len(active_connections) > 0:
                        print(f"Broadcasted metrics to {len(active_connections)} client(s)")
        except Exception as e:
            print(f"Error in broadcast_metrics: {e}")
        
        await asyncio.sleep(1)  # Check every 1 second for faster updates

@app.on_event("startup")
async def startup_event():
    """Start background task for broadcasting metrics"""
    asyncio.create_task(broadcast_metrics())

def _get_default_metrics():
    """Return default metrics when stats file doesn't exist"""
    return {
        "total_ingested": 0,
        "total_errors": 0,
        "by_project": {}
    }
