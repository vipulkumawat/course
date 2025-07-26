from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta
import asyncio
import random

from src.compression.delta_encoder import DeltaEncoder, DeltaDecoder
from src.compression.models import LogEntry, CompressionChunk
from src.storage.chunk_manager import ChunkManager
from config.delta_config import DeltaEncodingConfig

app = FastAPI(title="Delta Encoding Log System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
config = DeltaEncodingConfig.from_env()
encoder = DeltaEncoder(config)
decoder = DeltaDecoder()
chunk_manager = ChunkManager(config)

# Statistics tracking
system_stats = {
    'api_calls': 0,
    'compression_requests': 0,
    'decompression_requests': 0,
    'errors': 0,
    'start_time': datetime.now()
}

@app.get("/")
async def dashboard():
    """Serve the main dashboard"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Delta Encoding Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                         gap: 1.5rem; margin-bottom: 2rem; }
            .stat-card { background: white; padding: 1.5rem; border-radius: 8px; 
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .stat-value { font-size: 2rem; font-weight: bold; color: #667eea; margin-bottom: 0.5rem; }
            .stat-label { color: #666; font-size: 0.9rem; }
            .chart-container { background: white; padding: 1.5rem; border-radius: 8px; 
                              box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem; }
            .compression-demo { background: white; padding: 1.5rem; border-radius: 8px; 
                               box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            button { background: #667eea; color: white; border: none; padding: 0.75rem 1.5rem; 
                    border-radius: 6px; cursor: pointer; margin: 0.5rem; }
            button:hover { background: #5a67d8; }
            .demo-output { background: #f8f9fa; padding: 1rem; border-radius: 6px; 
                          font-family: monospace; margin-top: 1rem; max-height: 300px; overflow-y: auto; }
            .success { color: #28a745; }
            .error { color: #dc3545; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Delta Encoding Log System</h1>
                <p>Real-time compression monitoring and analytics dashboard</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="compression-ratio">--</div>
                    <div class="stat-label">Average Compression Ratio</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="storage-saved">--</div>
                    <div class="stat-label">Storage Saved (%)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="total-entries">--</div>
                    <div class="stat-label">Total Entries Processed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="chunks-count">--</div>
                    <div class="stat-label">Storage Chunks</div>
                </div>
            </div>
            
            <div class="compression-demo">
                <h3>Live Compression Demo</h3>
                <p>Test delta encoding with sample log entries:</p>
                
                <button onclick="generateSampleLogs()">Generate Sample Logs</button>
                <button onclick="compressLogs()">Compress with Delta Encoding</button>
                <button onclick="viewStats()">View Detailed Statistics</button>
                
                <div class="demo-output" id="demo-output">
                    <div class="success">Ready to demonstrate delta encoding...</div>
                </div>
            </div>
        </div>
        
        <script>
            let ws;
            let sampleLogs = [];
            
            function connectWebSocket() {
                try {
                    ws = new WebSocket('ws://localhost:8080/ws');
                    ws.onopen = function() {
                        console.log('WebSocket connected');
                    };
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        updateDashboard(data);
                    };
                    ws.onclose = function() {
                        console.log('WebSocket disconnected, retrying in 5 seconds...');
                        setTimeout(connectWebSocket, 5000);
                    };
                    ws.onerror = function(error) {
                        console.log('WebSocket error:', error);
                    };
                } catch (error) {
                    console.log('Failed to connect WebSocket:', error);
                    setTimeout(connectWebSocket, 5000);
                }
            }
            
            function updateDashboard(data) {
                document.getElementById('compression-ratio').textContent = 
                    (data.avg_compression_ratio * 100).toFixed(1) + '%';
                document.getElementById('storage-saved').textContent = 
                    data.storage_saved.toFixed(1);
                document.getElementById('total-entries').textContent = 
                    data.total_entries.toLocaleString();
                document.getElementById('chunks-count').textContent = 
                    data.total_chunks || 0;
            }
            
            function updateDashboardFromStats(statsData) {
                const compression = statsData.compression;
                const storage = statsData.storage;
                
                document.getElementById('compression-ratio').textContent = 
                    (compression.avg_compression_ratio * 100).toFixed(1) + '%';
                document.getElementById('storage-saved').textContent = 
                    compression.storage_saved.toFixed(1);
                document.getElementById('total-entries').textContent = 
                    compression.total_entries.toLocaleString();
                document.getElementById('chunks-count').textContent = 
                    storage.total_chunks || 0;
            }
            
            async function generateSampleLogs() {
                const output = document.getElementById('demo-output');
                output.innerHTML = '<div>Generating sample logs...</div>';
                
                try {
                    const response = await fetch('/api/generate-sample-logs', {method: 'POST'});
                    const data = await response.json();
                    sampleLogs = data.logs;
                    
                    output.innerHTML = `
                        <div class="success">Generated ${data.count} sample logs</div>
                        <div>Sample log preview:</div>
                        <pre>${JSON.stringify(data.logs[0], null, 2)}</pre>
                    `;
                } catch (error) {
                    output.innerHTML = `<div class="error">Error: ${error.message}</div>`;
                }
            }
            
            async function compressLogs() {
                if (sampleLogs.length === 0) {
                    document.getElementById('demo-output').innerHTML = 
                        '<div class="error">Please generate sample logs first</div>';
                    return;
                }
                
                const output = document.getElementById('demo-output');
                output.innerHTML = '<div>Compressing logs with delta encoding...</div>';
                
                try {
                    const response = await fetch('/api/compress-logs', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({logs: sampleLogs})
                    });
                    const data = await response.json();
                    
                    output.innerHTML = `
                        <div class="success">Compression completed!</div>
                        <div><strong>Original size:</strong> ${data.original_size} bytes</div>
                        <div><strong>Compressed size:</strong> ${data.compressed_size} bytes</div>
                        <div><strong>Compression ratio:</strong> ${(data.compression_ratio * 100).toFixed(1)}%</div>
                        <div><strong>Storage saved:</strong> ${data.storage_saved.toFixed(1)}%</div>
                        <div><strong>Baselines created:</strong> ${data.baselines_created}</div>
                        <div><strong>Delta entries:</strong> ${data.delta_entries}</div>
                    `;
                } catch (error) {
                    output.innerHTML = `<div class="error">Error: ${error.message}</div>`;
                }
            }
            
            async function viewStats() {
                try {
                    const response = await fetch('/api/stats');
                    const data = await response.json();
                    
                    document.getElementById('demo-output').innerHTML = `
                        <div><strong>System Statistics</strong></div>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                    `;
                } catch (error) {
                    document.getElementById('demo-output').innerHTML = 
                        `<div class="error">Error: ${error.message}</div>`;
                }
            }
            
            // Initialize
            connectWebSocket();
            
            // Auto-refresh stats every 5 seconds
            setInterval(async () => {
                try {
                    const response = await fetch('/api/stats');
                    const data = await response.json();
                    updateDashboardFromStats(data);
                } catch (error) {
                    console.error('Error fetching stats:', error);
                }
            }, 5000);
        </script>
    </body>
    </html>
    """)

@app.post("/api/generate-sample-logs")
async def generate_sample_logs():
    """Generate sample log entries for demonstration"""
    import random
    
    services = ['web-server', 'api-gateway', 'database', 'auth-service', 'payment-service']
    levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
    
    sample_logs = []
    base_time = datetime.now()
    
    # Generate 200 logs with more repetition for better compression
    for i in range(200):
        service = services[i % len(services)]  # Cycle through services
        level = levels[i % len(levels)]  # Cycle through levels
        
        # Create timestamp with small increments
        timestamp = (base_time + timedelta(seconds=i*2)).isoformat() + 'Z'
        
        # Create highly similar messages for better delta compression
        if service == 'web-server':
            message = f"HTTP 200 - /api/users/{i%5} - {random.randint(50, 150)}ms"
        elif service == 'api-gateway':
            message = f"Route request to {service} - correlation_id: req_{i%3}"
        elif service == 'database':
            message = f"Query executed - table: users - rows: {random.randint(10, 50)}"
        elif service == 'auth-service':
            message = f"User authentication - user_id: {i%10} - result: success"
        else:  # payment-service
            message = f"Payment processed - amount: ${random.randint(100, 500)} - status: completed"
        
        log_entry = LogEntry(
            timestamp=timestamp,
            level=level,
            service=service,
            message=message,
            metadata={
                'request_id': f"req_{i%5}",  # More repetition
                'user_id': f"user_{i%10}",   # More repetition
                'ip_address': f"192.168.1.{100 + (i%50)}",  # Smaller range
                'response_time_ms': random.randint(50, 200)  # Smaller range
            }
        )
        sample_logs.append(log_entry.to_dict())
    
    system_stats['api_calls'] += 1
    return {"logs": sample_logs, "count": len(sample_logs)}

@app.post("/api/compress-logs")
async def compress_logs(request: Dict[str, Any]):
    """Compress logs using delta encoding"""
    try:
        logs = request.get('logs', [])
        if not logs:
            raise HTTPException(status_code=400, detail="No logs provided")
        
        # Convert to LogEntry objects
        log_entries = [LogEntry.from_dict(log) for log in logs]
        
        # Group by service for better compression
        service_groups = {}
        for entry in log_entries:
            if entry.service not in service_groups:
                service_groups[entry.service] = []
            service_groups[entry.service].append(entry)
        
        total_original_size = 0
        total_compressed_size = 0
        baselines_created = 0
        delta_entries_created = 0
        
        # Process each service group
        for service, entries in service_groups.items():
            baseline = None
            original_size = sum(len(json.dumps(entry.to_dict()).encode()) for entry in entries)
            compressed_size = 0
            
            for i, entry in enumerate(entries):
                if i % config.baseline_frequency == 0 or baseline is None:
                    # Create new baseline
                    baseline = entry
                    baselines_created += 1
                    compressed_size += len(json.dumps(entry.to_dict()).encode())
                else:
                    # Create delta entry
                    delta_entry, compression_ratio = encoder.encode_entry(entry, baseline)
                    if delta_entry:
                        delta_entries_created += 1
                        # Only store the delta data, not the full delta entry structure
                        delta_data = delta_entry.field_deltas
                        compressed_size += len(json.dumps(delta_data).encode())
                    else:
                        # If no delta created, store full entry
                        compressed_size += len(json.dumps(entry.to_dict()).encode())
            
            total_original_size += original_size
            total_compressed_size += compressed_size
        
        overall_compression_ratio = total_compressed_size / total_original_size if total_original_size > 0 else 1.0
        storage_saved = (1 - overall_compression_ratio) * 100
        
        system_stats['compression_requests'] += 1
        
        return {
            'success': True,
            'original_size': total_original_size,
            'compressed_size': total_compressed_size,
            'compression_ratio': overall_compression_ratio,
            'storage_saved': storage_saved,
            'baselines_created': baselines_created,
            'delta_entries': delta_entries_created
        }
        
    except Exception as e:
        system_stats['errors'] += 1
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    compression_stats = encoder.get_stats()
    storage_stats = chunk_manager.get_storage_stats()
    
    uptime = (datetime.now() - system_stats['start_time']).total_seconds()
    
    return {
        'compression': compression_stats,
        'storage': storage_stats,
        'system': {
            **system_stats,
            'uptime_seconds': uptime,
            'uptime_formatted': f"{uptime//3600:.0f}h {(uptime%3600)//60:.0f}m"
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket for real-time updates"""
    try:
        await websocket.accept()
        print(f"WebSocket connection accepted from {websocket.client.host}")
        
        while True:
            try:
                stats = await get_stats()
                await websocket.send_text(json.dumps(stats['compression']))
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Error sending WebSocket data: {e}")
                break
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.dashboard_port)
