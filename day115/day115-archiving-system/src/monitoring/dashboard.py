from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import asyncio
from datetime import datetime
import structlog
import os

logger = structlog.get_logger()

class ArchivalDashboard:
    def __init__(self, archival_manager, storage_manager):
        self.app = FastAPI(title="Archival System Dashboard")
        self.archival_manager = archival_manager
        self.storage_manager = storage_manager
        self.active_connections = []
        
        # Mount static files if web directory exists
        web_static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "web", "static")
        if os.path.exists(web_static_path):
            self.app.mount("/static", StaticFiles(directory=web_static_path), name="static")
        
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.get("/")
        async def dashboard():
            return HTMLResponse(self._get_dashboard_html())
        
        @self.app.get("/api/stats")
        async def get_stats():
            archival_stats = self.archival_manager.get_statistics()
            storage_stats = await self.storage_manager.get_tier_statistics()
            
            return {
                "archival": archival_stats,
                "storage": storage_stats,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/api/jobs")
        async def get_jobs():
            return {
                "jobs": [self.archival_manager.get_job_status(job_id) 
                        for job_id in self.archival_manager.jobs.keys()],
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/favicon.ico")
        async def favicon():
            return {"message": "No favicon available"}
        
        @self.app.post("/api/trigger-archival")
        async def trigger_archival():
            """Manually trigger an archival cycle for testing"""
            try:
                # Import here to avoid circular imports
                from src.archival.scheduler import ArchivalScheduler
                temp_scheduler = ArchivalScheduler(self.archival_manager, self.archival_manager.config)
                await temp_scheduler.run_archival_cycle()
                return {"status": "success", "message": "Archival cycle completed"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    # Send real-time updates
                    stats = {
                        "archival": self.archival_manager.get_statistics(),
                        "storage": await self.storage_manager.get_tier_statistics(),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send_text(json.dumps(stats))
                    await asyncio.sleep(5)
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
    
    def _get_dashboard_html(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Archival System Dashboard</title>
            <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
            <meta http-equiv="Pragma" content="no-cache">
            <meta http-equiv="Expires" content="0">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: #2563eb; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .stat-value { font-size: 2em; font-weight: bold; color: #2563eb; }
                .stat-label { color: #666; margin-top: 5px; }
                .status-indicator { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
                .status-running { background: #10b981; }
                .status-idle { background: #f59e0b; }
                .jobs-section { margin-top: 30px; }
                .job-item { background: white; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid #2563eb; }
                .compression-bar { background: #e5e7eb; height: 20px; border-radius: 10px; overflow: hidden; }
                .compression-fill { background: #10b981; height: 100%; transition: width 0.3s; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📦 Historical Data Archiving System</h1>
                    <p>Real-time monitoring and management dashboard</p>
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center;">
                            <span class="status-indicator status-running"></span>
                            <span>System Status: Active</span>
                        </div>
                        <div style="display: flex; gap: 10px;">
                            <button onclick="triggerArchival()" style="background: #10b981; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                                🔄 Trigger Archival
                            </button>
                            <button onclick="refreshDashboard()" style="background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                                🔄 Refresh Data
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="total-archived">0</div>
                        <div class="stat-label">Total Logs Archived</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="compression-ratio">0%</div>
                        <div class="stat-label">Average Compression Ratio</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="storage-saved">0 MB</div>
                        <div class="stat-label">Storage Space Saved</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="active-jobs">0</div>
                        <div class="stat-label">Active Archival Jobs</div>
                    </div>
                </div>
                
                <div class="jobs-section">
                    <h2>Storage Tier Distribution</h2>
                    <div class="stats-grid" id="storage-tiers">
                        <!-- Storage tier stats will be populated here -->
                    </div>
                </div>
                
                <div class="jobs-section">
                    <h2>Recent Archival Jobs</h2>
                    <div id="recent-jobs">
                        <!-- Jobs will be populated here -->
                    </div>
                </div>
            </div>
            
            <script>
                // Version: 2025-09-24-06-10
                // Disable WebSocket for now to avoid conflicts
                // const ws = new WebSocket('ws://localhost:8001/ws');
                
                function updateDashboard(data) {
                    // Update main stats
                    document.getElementById('total-archived').textContent = 
                        data.archival.total_archived.toLocaleString();
                    
                    const compressionRatio = (1 - data.archival.compression_ratio) * 100;
                    document.getElementById('compression-ratio').textContent = 
                        compressionRatio.toFixed(1) + '%';
                    
                    const spaceSaved = (data.archival.total_original_size - data.archival.total_compressed_size) / (1024 * 1024);
                    document.getElementById('storage-saved').textContent = 
                        spaceSaved.toFixed(1) + ' MB';
                    
                    // Update active jobs count
                    document.getElementById('active-jobs').textContent = 
                        data.jobs ? data.jobs.filter(job => job && job.status === 'processing').length : 0;
                    
                    // Update storage tiers
                    const storageTiersElement = document.getElementById('storage-tiers');
                    storageTiersElement.innerHTML = '';
                    
                    for (const [tier, stats] of Object.entries(data.storage)) {
                        const tierCard = document.createElement('div');
                        tierCard.className = 'stat-card';
                        tierCard.innerHTML = `
                            <div class="stat-value">${stats.file_count}</div>
                            <div class="stat-label">${tier.toUpperCase()} Storage - ${stats.total_size_mb} MB</div>
                        `;
                        storageTiersElement.appendChild(tierCard);
                    }
                    
                    // Update recent jobs
                    updateRecentJobs(data.jobs || []);
                }
                
                function updateRecentJobs(jobs) {
                    const recentJobsElement = document.getElementById('recent-jobs');
                    recentJobsElement.innerHTML = '';
                    
                    if (jobs.length === 0) {
                        recentJobsElement.innerHTML = '<div class="job-item">No archival jobs found. Click "Trigger Archival" to start processing logs.</div>';
                        return;
                    }
                    
                    // Sort jobs by creation date (newest first) and limit to 10
                    const sortedJobs = jobs
                        .filter(job => job !== null)
                        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                        .slice(0, 10);
                    
                    sortedJobs.forEach(job => {
                        const jobElement = document.createElement('div');
                        jobElement.className = 'job-item';
                        
                        const statusColor = {
                            'completed': '#10b981',
                            'processing': '#f59e0b',
                            'failed': '#ef4444',
                            'created': '#6b7280'
                        }[job.status] || '#6b7280';
                        
                        const compressionPercent = ((1 - job.compression_ratio) * 100).toFixed(1);
                        
                        jobElement.innerHTML = `
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <div>
                                    <strong>Job ${job.job_id}</strong>
                                    <span style="margin-left: 10px; padding: 4px 8px; border-radius: 4px; background: ${statusColor}; color: white; font-size: 0.8em;">
                                        ${job.status.toUpperCase()}
                                    </span>
                                </div>
                                <div style="color: #666; font-size: 0.9em;">
                                    ${new Date(job.created_at).toLocaleString()}
                                </div>
                            </div>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; font-size: 0.9em;">
                                <div>Entries: ${job.entries ? job.entries.length : 0}</div>
                                <div>Compression: ${compressionPercent}%</div>
                                <div>Tier: ${job.storage_tier || 'N/A'}</div>
                            </div>
                            ${job.status === 'processing' ? `
                                <div style="margin-top: 10px;">
                                    <div class="compression-bar">
                                        <div class="compression-fill" style="width: 50%;"></div>
                                    </div>
                                </div>
                            ` : ''}
                        `;
                        recentJobsElement.appendChild(jobElement);
                    });
                }
                
                // Initial load
                Promise.all([
                    fetch('/api/stats').then(response => response.json()),
                    fetch('/api/jobs').then(response => response.json())
                ]).then(([statsData, jobsData]) => {
                    const combinedData = {
                        ...statsData,
                        jobs: jobsData.jobs
                    };
                    updateDashboard(combinedData);
                });
                
                // Trigger archival function
                function triggerArchival() {
                    const button = event.target;
                    const originalText = button.textContent;
                    button.textContent = '⏳ Processing...';
                    button.disabled = true;
                    
                    console.log('Triggering archival process...');
                    
                    fetch('/api/trigger-archival', { method: 'POST' })
                        .then(response => response.json())
                        .then(data => {
                            console.log('Archival response:', data);
                            if (data.status === 'success') {
                                button.textContent = '✅ Completed';
                                
                                // Immediate refresh
                                refreshDashboard();
                                
                                // Additional refresh after delay to ensure data is updated
                                setTimeout(() => {
                                    refreshDashboard();
                                }, 2000);
                                
                                // Final refresh
                                setTimeout(() => {
                                    refreshDashboard();
                                }, 5000);
                            } else {
                                button.textContent = '❌ Error';
                                console.error('Archival failed:', data.message);
                            }
                        })
                        .catch(error => {
                            button.textContent = '❌ Error';
                            console.error('Archival failed:', error);
                        })
                        .finally(() => {
                            setTimeout(() => {
                                button.textContent = originalText;
                                button.disabled = false;
                            }, 3000);
                        });
                }
                
                // Function to refresh dashboard data
                function refreshDashboard() {
                    console.log('Refreshing dashboard...');
                    const refreshButton = document.querySelector('button[onclick="refreshDashboard()"]');
                    if (refreshButton) {
                        refreshButton.textContent = '🔄 Refreshing...';
                        refreshButton.disabled = true;
                    }
                    
                    Promise.all([
                        fetch('/api/stats').then(response => response.json()),
                        fetch('/api/jobs').then(response => response.json())
                    ]).then(([statsData, jobsData]) => {
                        console.log('Stats data:', statsData);
                        console.log('Jobs data:', jobsData);
                        const combinedData = {
                            ...statsData,
                            jobs: jobsData.jobs
                        };
                        updateDashboard(combinedData);
                        
                        // Show success message
                        if (refreshButton) {
                            refreshButton.textContent = '✅ Refreshed';
                            setTimeout(() => {
                                refreshButton.textContent = '🔄 Refresh Data';
                                refreshButton.disabled = false;
                            }, 1000);
                        }
                    }).catch(error => {
                        console.error('Error refreshing dashboard:', error);
                        if (refreshButton) {
                            refreshButton.textContent = '❌ Error';
                            setTimeout(() => {
                                refreshButton.textContent = '🔄 Refresh Data';
                                refreshButton.disabled = false;
                            }, 2000);
                        }
                    });
                }
                
                // Auto-refresh every 10 seconds
                setInterval(refreshDashboard, 10000);
            </script>
        </body>
        </html>
        """
