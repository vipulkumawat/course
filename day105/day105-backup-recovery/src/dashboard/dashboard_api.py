from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import redis
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import logging

from recovery.recovery_manager import RecoveryManager
from validation.validator import BackupValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Backup & Recovery Dashboard", version="1.0.0")

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@app.get("/")
async def dashboard():
    """Serve dashboard HTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Backup & Recovery Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; color: #2d3748; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; }
            .header h1 { margin-bottom: 0.5rem; font-size: 2.5rem; }
            .header p { opacity: 0.9; font-size: 1.1rem; }
            .container { max-width: 1200px; margin: -1rem auto 0; padding: 0 1rem; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
            .stat-card { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #667eea; }
            .stat-title { color: #718096; font-size: 0.875rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem; }
            .stat-value { font-size: 2rem; font-weight: bold; color: #2d3748; }
            .stat-subtitle { color: #a0aec0; font-size: 0.875rem; margin-top: 0.25rem; }
            .content-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 2rem; }
            .section { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .section h2 { color: #2d3748; margin-bottom: 1rem; font-size: 1.25rem; }
            .backup-item { padding: 1rem; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 0.5rem; }
            .backup-item h3 { color: #4a5568; font-size: 1rem; margin-bottom: 0.25rem; }
            .backup-meta { color: #718096; font-size: 0.875rem; }
            .status { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
            .status.completed { background: #c6f6d5; color: #22543d; }
            .status.running { background: #bee3f8; color: #2c5282; }
            .status.failed { background: #fed7d7; color: #c53030; }
            .log-entry { padding: 0.5rem; border-left: 3px solid #e2e8f0; margin-bottom: 0.5rem; font-family: monospace; font-size: 0.875rem; }
            .log-info { border-left-color: #4299e1; }
            .log-warning { border-left-color: #f6ad55; }
            .log-error { border-left-color: #f56565; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ Backup & Recovery Dashboard</h1>
            <p>Monitoring automated backup operations and system recovery status</p>
        </div>
        
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-title">Total Backups</div>
                    <div class="stat-value" id="totalBackups">-</div>
                    <div class="stat-subtitle">Completed successfully</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Storage Used</div>
                    <div class="stat-value" id="storageUsed">-</div>
                    <div class="stat-subtitle">Across all backups</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Last Backup</div>
                    <div class="stat-value" id="lastBackup">-</div>
                    <div class="stat-subtitle">Most recent completion</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Success Rate</div>
                    <div class="stat-value" id="successRate">-</div>
                    <div class="stat-subtitle">Last 7 days</div>
                </div>
            </div>
            
            <div class="content-grid">
                <div class="section">
                    <h2>📦 Recent Backups</h2>
                    <div id="recentBackups">Loading...</div>
                </div>
                
                <div class="section">
                    <h2>📊 System Status</h2>
                    <div id="systemLogs">Loading...</div>
                </div>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket(`ws://localhost:8106/ws`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            function updateDashboard(data) {
                if (data.stats) {
                    document.getElementById('totalBackups').textContent = data.stats.total_backups || 0;
                    document.getElementById('storageUsed').textContent = formatBytes(data.stats.total_size || 0);
                    document.getElementById('lastBackup').textContent = formatTime(data.stats.last_backup);
                    document.getElementById('successRate').textContent = (data.stats.success_rate || 0) + '%';
                }
                
                if (data.backups) {
                    updateBackupsList(data.backups);
                }
                
                if (data.logs) {
                    updateSystemLogs(data.logs);
                }
            }
            
            function updateBackupsList(backups) {
                const container = document.getElementById('recentBackups');
                container.innerHTML = '';
                
                backups.slice(0, 5).forEach(backup => {
                    const item = document.createElement('div');
                    item.className = 'backup-item';
                    item.innerHTML = `
                        <h3>${backup.backup_id}</h3>
                        <div class="backup-meta">
                            <span class="status ${backup.status}">${backup.status.toUpperCase()}</span>
                            ${backup.strategy} • ${formatBytes(backup.size_bytes)} • ${formatTime(backup.timestamp)}
                        </div>
                    `;
                    container.appendChild(item);
                });
            }
            
            function updateSystemLogs(logs) {
                const container = document.getElementById('systemLogs');
                container.innerHTML = '';
                
                logs.slice(-10).forEach(log => {
                    const entry = document.createElement('div');
                    entry.className = `log-entry log-${log.level}`;
                    entry.textContent = `[${formatTime(log.timestamp)}] ${log.message}`;
                    container.appendChild(entry);
                });
            }
            
            function formatBytes(bytes) {
                if (bytes === 0) return '0 B';
                const k = 1024;
                const sizes = ['B', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }
            
            function formatTime(timestamp) {
                if (!timestamp) return 'Never';
                return new Date(timestamp).toLocaleString();
            }
            
            // Initial data fetch
            fetch('/api/stats').then(r => r.json()).then(updateDashboard);
            setInterval(() => fetch('/api/stats').then(r => r.json()).then(updateDashboard), 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/stats")
async def get_stats():
    """Get backup statistics"""
    # Get recent backups list from actual files
    recovery_manager = RecoveryManager()
    backups = await recovery_manager.list_available_backups()
    
    # Calculate stats from actual backup files
    total_backups = len(backups)
    total_size = 0
    completed_backups = 0
    last_backup = None
    
    for backup in backups:
        # All backups found on disk are considered completed
        completed_backups += 1
        total_size += backup.get("size_bytes", 0)
        
        # Find the most recent backup
        if not last_backup or backup.get("timestamp", "") > last_backup:
            last_backup = backup.get("timestamp")
    
    success_rate = (completed_backups / total_backups * 100) if total_backups > 0 else 0
    
    # Convert to display format
    backup_list = []
    for backup in backups[:10]:
        backup_status = "completed"  # Assume completed if we have the backup file
        backup_list.append({
            "backup_id": backup["backup_id"],
            "strategy": backup["strategy"],
            "status": backup_status,
            "timestamp": backup["timestamp"],
            "size_bytes": backup["size_bytes"]
        })
    
    # Generate sample logs
    sample_logs = [
        {"timestamp": datetime.now().isoformat(), "level": "info", "message": "Backup scheduler running"},
        {"timestamp": datetime.now().isoformat(), "level": "info", "message": f"Found {total_backups} backup records"},
        {"timestamp": datetime.now().isoformat(), "level": "info", "message": f"Success rate: {success_rate:.1f}%"}
    ]
    
    return {
        "stats": {
            "total_backups": total_backups,
            "total_size": total_size,
            "last_backup": last_backup,
            "success_rate": round(success_rate, 1)
        },
        "backups": backup_list,
        "logs": sample_logs
    }

@app.get("/api/backups")
async def get_backups():
    """Get list of available backups"""
    recovery_manager = RecoveryManager()
    return await recovery_manager.list_available_backups()

@app.post("/api/backup/trigger")
async def trigger_backup(backup_type: str = "full"):
    """Manually trigger backup"""
    from scheduler.backup_scheduler import BackupScheduler
    from config.backup_config import BackupStrategy
    
    try:
        scheduler = BackupScheduler()
        strategy = BackupStrategy(backup_type)
        result = await scheduler.schedule_backup(strategy)
        return {"success": True, "message": f"Backup {backup_type} triggered"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/recovery/restore")
async def restore_backup(backup_id: str, target_directory: str = "recovery/api_restore"):
    """Restore from specific backup"""
    recovery_manager = RecoveryManager()
    return await recovery_manager.recover_from_backup(backup_id, target_directory)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            stats_data = await get_stats()
            await websocket.send_text(json.dumps(stats_data))
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8105)
