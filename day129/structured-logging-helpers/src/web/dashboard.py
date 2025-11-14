"""Real-time structured logging dashboard."""
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
import json
import asyncio
from typing import List, Dict, Any
import time
from datetime import datetime


class LoggingDashboard:
    """Real-time dashboard for structured logging helpers."""
    
    def __init__(self):
        self.app = FastAPI(title="Structured Logging Dashboard")
        self.active_connections: List[WebSocket] = []
        self.log_stats = {
            'total_logs': 0,
            'logs_by_level': {'debug': 0, 'info': 0, 'warning': 0, 'error': 0, 'critical': 0},
            'validation_errors': 0,
            'context_injections': 0,
            'serialization_cache_hits': 0
        }
        self.recent_logs = []
        self.setup_routes()
        
    def setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            return self.get_dashboard_html()
            
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except:
                self.active_connections.remove(websocket)
                
        @self.app.get("/api/stats")
        async def get_stats():
            return self.log_stats
            
        @self.app.get("/api/logs")
        async def get_recent_logs():
            return self.recent_logs[-50:]  # Last 50 logs
            
        @self.app.post("/api/test-log")
        async def test_log(request: Request):
            data = await request.json()
            await self.process_test_log(data)
            return {"status": "processed"}
            
        @self.app.get("/favicon.ico")
        async def favicon():
            """Return a simple SVG favicon."""
            svg_icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <rect width="100" height="100" fill="#2c3e50"/>
                <text x="50" y="70" font-size="60" fill="#27ae60" text-anchor="middle" font-family="Arial">📊</text>
            </svg>"""
            return Response(content=svg_icon, media_type="image/svg+xml")
            
    async def process_test_log(self, log_data: Dict[str, Any]):
        """Process a test log entry."""
        self.log_stats['total_logs'] += 1
        
        level = log_data.get('level', 'info')
        if level in self.log_stats['logs_by_level']:
            self.log_stats['logs_by_level'][level] += 1
            
        # Check for validation errors
        if any('validation_error' in key for key in log_data.get('fields', {}).keys()):
            self.log_stats['validation_errors'] += 1
            
        # Check for context injection
        if log_data.get('context'):
            self.log_stats['context_injections'] += 1
            
        # Add to recent logs
        log_data['processed_at'] = datetime.now().isoformat()
        self.recent_logs.append(log_data)
        
        # Keep only last 100 logs
        if len(self.recent_logs) > 100:
            self.recent_logs = self.recent_logs[-100:]
            
        # Broadcast to connected clients
        await self.broadcast_update({
            'type': 'new_log',
            'log': log_data,
            'stats': self.log_stats
        })
        
    async def broadcast_update(self, message: Dict[str, Any]):
        """Broadcast update to all connected WebSocket clients."""
        if self.active_connections:
            message_json = json.dumps(message)
            disconnected = []
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_json)
                except:
                    disconnected.append(connection)
                    
            # Remove disconnected clients
            for connection in disconnected:
                self.active_connections.remove(connection)
                
    def get_dashboard_html(self) -> str:
        """Return dashboard HTML."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Structured Logging Dashboard</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
            <link rel="icon" href="/favicon.ico" type="image/svg+xml">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #ecf0f1 0%, #bdc3c7 100%);
                    min-height: 100vh;
                    color: #2c3e50;
                }
                
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                }
                
                .header {
                    background: rgba(255, 255, 255, 0.95);
                    padding: 20px;
                    border-radius: 15px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    margin-bottom: 20px;
                    backdrop-filter: blur(10px);
                }
                
                .header h1 {
                    color: #4a5568;
                    font-size: 2.5em;
                    font-weight: 700;
                    text-align: center;
                    margin-bottom: 10px;
                }
                
                .header p {
                    text-align: center;
                    color: #718096;
                    font-size: 1.1em;
                }
                
                .dashboard-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 20px;
                }
                
                .card {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 20px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    backdrop-filter: blur(10px);
                    transition: transform 0.3s ease;
                }
                
                .card:hover {
                    transform: translateY(-5px);
                }
                
                .card h3 {
                    color: #4a5568;
                    margin-bottom: 15px;
                    font-size: 1.3em;
                    font-weight: 600;
                }
                
                .stat-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                }
                
                .stat-item {
                    text-align: center;
                    padding: 15px;
                    background: linear-gradient(45deg, #f7fafc, #edf2f7);
                    border-radius: 10px;
                    border: 2px solid #e2e8f0;
                }
                
                .stat-value {
                    font-size: 2em;
                    font-weight: bold;
                    color: #2d3748;
                }
                
                .stat-label {
                    color: #718096;
                    font-size: 0.9em;
                    margin-top: 5px;
                }
                
                .log-entry {
                    background: #f8f9fa;
                    border-left: 4px solid #27ae60;
                    padding: 12px;
                    margin-bottom: 10px;
                    border-radius: 8px;
                    font-family: 'Courier New', monospace;
                    font-size: 0.9em;
                }
                
                .log-entry.error {
                    border-left-color: #e53e3e;
                    background: #fed7d7;
                }
                
                .log-entry.warning {
                    border-left-color: #d69e2e;
                    background: #fef5e7;
                }
                
                .test-panel {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 20px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                }
                
                .test-buttons {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 10px;
                    margin-top: 15px;
                }
                
                .test-btn {
                    padding: 12px 20px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: all 0.3s ease;
                }
                
                .test-btn.info {
                    background: linear-gradient(45deg, #27ae60, #229954);
                    color: white;
                }
                
                .test-btn.warning {
                    background: linear-gradient(45deg, #d69e2e, #b7791f);
                    color: white;
                }
                
                .test-btn.error {
                    background: linear-gradient(45deg, #e53e3e, #c53030);
                    color: white;
                }
                
                .test-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }
                
                .connection-status {
                    padding: 8px 15px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    font-weight: 600;
                    display: inline-block;
                }
                
                .connected {
                    background: #c6f6d5;
                    color: #22543d;
                }
                
                .disconnected {
                    background: #fed7d7;
                    color: #742a2a;
                }
                
                .logs-container {
                    max-height: 400px;
                    overflow-y: auto;
                    background: #f8f9fa;
                    border-radius: 10px;
                    padding: 15px;
                }
                
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                    100% { transform: scale(1); }
                }
                
                .pulse {
                    animation: pulse 0.5s ease-in-out;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔧 Structured Logging Dashboard</h1>
                    <p>Real-time monitoring of structured log processing with validation and context injection</p>
                    <div style="text-align: center; margin-top: 15px;">
                        <span id="connection-status" class="connection-status disconnected">⚠️ Connecting...</span>
                    </div>
                </div>
                
                <div class="dashboard-grid">
                    <div class="card">
                        <h3>📊 Processing Statistics</h3>
                        <div class="stat-grid">
                            <div class="stat-item">
                                <div class="stat-value" id="total-logs">0</div>
                                <div class="stat-label">Total Logs</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value" id="validation-errors">0</div>
                                <div class="stat-label">Validation Errors</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value" id="context-injections">0</div>
                                <div class="stat-label">Context Injections</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value" id="cache-hits">0</div>
                                <div class="stat-label">Cache Hits</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>📈 Log Level Distribution</h3>
                        <div id="level-chart" style="height: 200px;"></div>
                    </div>
                </div>
                
                <div class="test-panel">
                    <h3>🧪 Test Structured Logging</h3>
                    <p>Generate test logs to see validation and context injection in action</p>
                    <div class="test-buttons">
                        <button class="test-btn info" onclick="sendTestLog('info')">📘 Info Log</button>
                        <button class="test-btn warning" onclick="sendTestLog('warning')">⚠️ Warning Log</button>
                        <button class="test-btn error" onclick="sendTestLog('error')">🚨 Error Log</button>
                        <button class="test-btn info" onclick="sendTestLog('validation')">🔍 Validation Test</button>
                    </div>
                </div>
                
                <div class="card" style="margin-top: 20px;">
                    <h3>📝 Recent Log Entries</h3>
                    <div id="logs-container" class="logs-container">
                        <p style="color: #718096; text-align: center; padding: 20px;">
                            No logs yet. Click the test buttons above to generate some!
                        </p>
                    </div>
                </div>
            </div>
            
            <script>
                let ws;
                let stats = {
                    total_logs: 0,
                    logs_by_level: {debug: 0, info: 0, warning: 0, error: 0, critical: 0},
                    validation_errors: 0,
                    context_injections: 0,
                    serialization_cache_hits: 0
                };
                
                function connectWebSocket() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
                    
                    ws.onopen = function() {
                        document.getElementById('connection-status').className = 'connection-status connected';
                        document.getElementById('connection-status').textContent = '✅ Connected';
                    };
                    
                    ws.onclose = function() {
                        document.getElementById('connection-status').className = 'connection-status disconnected';
                        document.getElementById('connection-status').textContent = '❌ Disconnected';
                        setTimeout(connectWebSocket, 3000);
                    };
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        if (data.type === 'new_log') {
                            updateStats(data.stats);
                            addLogEntry(data.log);
                        }
                    };
                }
                
                function updateStats(newStats) {
                    stats = newStats;
                    document.getElementById('total-logs').textContent = stats.total_logs;
                    document.getElementById('validation-errors').textContent = stats.validation_errors;
                    document.getElementById('context-injections').textContent = stats.context_injections;
                    document.getElementById('cache-hits').textContent = stats.serialization_cache_hits;
                    
                    // Pulse effect on update
                    document.querySelector('.stat-grid').classList.add('pulse');
                    setTimeout(() => document.querySelector('.stat-grid').classList.remove('pulse'), 500);
                    
                    updateLevelChart();
                }
                
                function updateLevelChart() {
                    const levels = Object.keys(stats.logs_by_level);
                    const values = Object.values(stats.logs_by_level);
                    
                    const data = [{
                        x: levels,
                        y: values,
                        type: 'bar',
                        marker: {
                            color: ['#27ae60', '#2ecc71', '#f39c12', '#e74c3c', '#95a5a6']
                        }
                    }];
                    
                    const layout = {
                        margin: { t: 10, r: 10, b: 30, l: 30 },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { size: 11 }
                    };
                    
                    Plotly.newPlot('level-chart', data, layout, {displayModeBar: false});
                }
                
                function addLogEntry(log) {
                    const container = document.getElementById('logs-container');
                    
                    // Clear "no logs" message
                    if (container.children.length === 1 && container.children[0].tagName === 'P') {
                        container.innerHTML = '';
                    }
                    
                    const entry = document.createElement('div');
                    entry.className = `log-entry ${log.level}`;
                    entry.innerHTML = `
                        <strong>${log.timestamp}</strong> [${log.level.toUpperCase()}] ${log.message}
                        <br><small>Service: ${log.service_name} | Trace: ${log.trace_id}</small>
                        ${log.fields && Object.keys(log.fields).length > 0 ? 
                            `<br><small>Fields: ${JSON.stringify(log.fields)}</small>` : ''}
                    `;
                    
                    container.insertBefore(entry, container.firstChild);
                    
                    // Keep only last 20 entries visible
                    while (container.children.length > 20) {
                        container.removeChild(container.lastChild);
                    }
                }
                
                async function sendTestLog(type) {
                    const testLogs = {
                        info: {
                            level: 'info',
                            message: 'User logged in successfully',
                            fields: {
                                user_id: 12345,
                                email: 'user@example.com',
                                ip_address: '192.168.1.100'
                            }
                        },
                        warning: {
                            level: 'warning',
                            message: 'High response time detected',
                            fields: {
                                response_time: 2.5,
                                endpoint: '/api/users',
                                status_code: 200
                            }
                        },
                        error: {
                            level: 'error',
                            message: 'Payment processing failed',
                            fields: {
                                user_id: 67890,
                                amount: 99.99,
                                error_code: 'CARD_DECLINED'
                            }
                        },
                        validation: {
                            level: 'info',
                            message: 'Test validation errors',
                            fields: {
                                user_id: 'invalid_id',  // Should be int
                                email: 'invalid-email',  // Invalid format
                                amount: -50,  // Invalid range
                                response_time: 999  // Out of range
                            }
                        }
                    };
                    
                    const logData = testLogs[type];
                    logData.service_name = 'test-service';
                    logData.trace_id = 'test-' + Date.now();
                    logData.timestamp = new Date().toISOString();
                    logData.context = {
                        hostname: 'localhost',
                        environment: 'development'
                    };
                    
                    try {
                        const response = await fetch('/api/test-log', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(logData)
                        });
                        
                        if (!response.ok) {
                            console.error('Failed to send test log');
                        }
                    } catch (error) {
                        console.error('Error sending test log:', error);
                    }
                }
                
                // Initialize
                connectWebSocket();
                updateLevelChart();
            </script>
        </body>
        </html>
        """


# Create dashboard instance
dashboard = LoggingDashboard()
app = dashboard.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
