#!/bin/bash
set -e  # Exit on any error

echo "🚀 Day 91: Implementing Batch API Operations for Distributed Log Processing"
echo "============================================================================"

# Create project structure
echo "📁 Creating project structure..."
mkdir -p day91-batch-api-operations/{src/{api,batch,models,utils,monitoring},tests/{unit,integration,performance},static/{css,js},templates,config,docker}

cd day91-batch-api-operations

# Create directory verification
echo "📂 Verifying directory structure..."
find . -type d | sort

# Create requirements.txt with latest May 2025 compatible libraries
echo "📦 Creating requirements.txt with latest libraries..."
cat > requirements.txt << 'EOF'
fastapi==0.111.0
uvicorn[standard]==0.30.1
pydantic==2.7.1
sqlalchemy==2.0.30
asyncpg==0.29.0
redis==5.0.4
pytest==8.2.0
pytest-asyncio==0.23.7
httpx==0.27.0
psutil==5.9.8
aiofiles==23.2.1
jinja2==3.1.4
python-multipart==0.0.9
structlog==24.1.0
prometheus-client==0.20.0
EOF

# Create start.sh script
cat > start.sh << 'EOF'
#!/bin/bash
echo "🔧 Starting Day 91 Batch API Operations System..."

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python 3.11 virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database setup
echo "🗄️ Setting up database..."
python src/utils/database_setup.py

# Start Redis if not running
echo "🔴 Starting Redis..."
redis-server --daemonize yes --port 6379 || echo "Redis already running"

# Start the API server
echo "🚀 Starting Batch API server..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

echo "API_PID=$API_PID" > .pids

# Start monitoring dashboard
echo "📊 Starting monitoring dashboard..."
python src/monitoring/dashboard.py &
MONITOR_PID=$!

echo "MONITOR_PID=$MONITOR_PID" >> .pids

echo "✅ System started successfully!"
echo "📡 API Server: http://localhost:8000"
echo "📊 Monitoring Dashboard: http://localhost:8001"
echo "📚 API Documentation: http://localhost:8000/docs"

# Wait for services to be ready
sleep 5

# Run demonstration
echo "🎬 Running demonstration..."
python src/utils/demo.py

echo "Press Ctrl+C to stop all services"
wait
EOF

# Create stop.sh script
cat > stop.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Day 91 Batch API Operations System..."

if [ -f .pids ]; then
    source .pids
    
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$MONITOR_PID" ]; then
        kill $MONITOR_PID 2>/dev/null || true
    fi
    
    rm .pids
fi

# Stop any remaining processes
pkill -f "uvicorn src.api.main" 2>/dev/null || true
pkill -f "python src/monitoring/dashboard.py" 2>/dev/null || true

echo "✅ All services stopped"
EOF

chmod +x start.sh stop.sh

# Create main API module
echo "🔧 Creating main API module..."
cat > src/api/main.py << 'EOF'
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any, Optional
import asyncio
import time
import json
import logging
from datetime import datetime, timezone

from ..batch.batch_processor import BatchProcessor
from ..models.log_models import LogEntry, BatchRequest, BatchResponse, BatchStats
from ..monitoring.metrics import MetricsCollector
from ..utils.database import get_db_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Distributed Log Processing - Batch API",
    description="High-performance batch operations for log processing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize components
batch_processor = BatchProcessor()
metrics = MetricsCollector()

@app.on_startup
async def startup_event():
    """Initialize system on startup"""
    logger.info("🚀 Starting Batch API Operations System")
    await batch_processor.initialize()
    metrics.start_collection()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request):
    """Main dashboard page"""
    stats = await metrics.get_current_stats()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats
    })

@app.post("/api/v1/logs/batch", response_model=BatchResponse)
async def batch_insert_logs(
    batch_request: BatchRequest,
    background_tasks: BackgroundTasks,
    db_session = Depends(get_db_session)
):
    """Insert multiple log entries in a single batch operation"""
    start_time = time.time()
    
    try:
        logger.info(f"📦 Processing batch of {len(batch_request.logs)} log entries")
        
        # Validate batch size
        if len(batch_request.logs) > 10000:
            raise HTTPException(
                status_code=400,
                detail="Batch size exceeds maximum limit of 10000 entries"
            )
        
        # Process batch
        result = await batch_processor.process_batch_insert(
            batch_request.logs,
            db_session,
            chunk_size=batch_request.chunk_size or 1000
        )
        
        # Record metrics
        processing_time = time.time() - start_time
        background_tasks.add_task(
            metrics.record_batch_operation,
            "insert", len(batch_request.logs), processing_time, result.success_count
        )
        
        return BatchResponse(
            success=result.success_count == len(batch_request.logs),
            total_processed=len(batch_request.logs),
            success_count=result.success_count,
            error_count=result.error_count,
            errors=result.errors,
            processing_time=processing_time,
            batch_id=result.batch_id
        )
        
    except Exception as e:
        logger.error(f"❌ Batch insert failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/logs/batch/query", response_model=Dict[str, Any])
async def batch_query_logs(
    query_request: Dict[str, Any],
    db_session = Depends(get_db_session)
):
    """Query multiple log entries with batch optimization"""
    start_time = time.time()
    
    try:
        result = await batch_processor.process_batch_query(
            query_request,
            db_session
        )
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "total_results": len(result.logs),
            "logs": [log.dict() for log in result.logs],
            "processing_time": processing_time,
            "query_stats": result.query_stats
        }
        
    except Exception as e:
        logger.error(f"❌ Batch query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/logs/batch", response_model=BatchResponse)
async def batch_delete_logs(
    delete_request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db_session = Depends(get_db_session)
):
    """Delete multiple log entries in a single batch operation"""
    start_time = time.time()
    
    try:
        result = await batch_processor.process_batch_delete(
            delete_request,
            db_session
        )
        
        processing_time = time.time() - start_time
        background_tasks.add_task(
            metrics.record_batch_operation,
            "delete", result.total_processed, processing_time, result.success_count
        )
        
        return BatchResponse(
            success=result.success_count == result.total_processed,
            total_processed=result.total_processed,
            success_count=result.success_count,
            error_count=result.error_count,
            errors=result.errors,
            processing_time=processing_time,
            batch_id=result.batch_id
        )
        
    except Exception as e:
        logger.error(f"❌ Batch delete failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/metrics/batch", response_model=BatchStats)
async def get_batch_metrics():
    """Get current batch operation metrics"""
    return await metrics.get_batch_stats()

@app.get("/api/v1/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "batch_processor": await batch_processor.health_check(),
        "metrics_collector": metrics.is_healthy()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Create batch processor
echo "⚙️ Creating batch processor..."
cat > src/batch/batch_processor.py << 'EOF'
import asyncio
import asyncpg
import json
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
import logging

from ..models.log_models import LogEntry, BatchResult, QueryResult

logger = logging.getLogger(__name__)

@dataclass
class ProcessingChunk:
    chunk_id: str
    logs: List[LogEntry]
    start_index: int
    end_index: int

class BatchProcessor:
    def __init__(self):
        self.db_pool = None
        self.max_chunk_size = 1000
        self.max_concurrent_chunks = 10
        
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(
                host='localhost',
                port=5432,
                user='postgres',
                password='postgres',
                database='logdb',
                min_size=5,
                max_size=20
            )
            logger.info("✅ Database connection pool initialized")
        except Exception as e:
            logger.warning(f"⚠️ Database connection failed, using in-memory storage: {e}")
            self.db_pool = None
    
    async def process_batch_insert(
        self, 
        logs: List[LogEntry], 
        db_session,
        chunk_size: int = 1000
    ) -> BatchResult:
        """Process batch insert with chunking and parallel execution"""
        batch_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Split into chunks
            chunks = self._create_chunks(logs, chunk_size, batch_id)
            logger.info(f"📊 Split {len(logs)} logs into {len(chunks)} chunks")
            
            # Process chunks in parallel
            semaphore = asyncio.Semaphore(self.max_concurrent_chunks)
            tasks = [
                self._process_insert_chunk(chunk, semaphore)
                for chunk in chunks
            ]
            
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Aggregate results
            success_count = 0
            error_count = 0
            errors = []
            
            for i, result in enumerate(chunk_results):
                if isinstance(result, Exception):
                    error_count += len(chunks[i].logs)
                    errors.append(f"Chunk {chunks[i].chunk_id}: {str(result)}")
                else:
                    success_count += result.get('success_count', 0)
                    error_count += result.get('error_count', 0)
                    if result.get('errors'):
                        errors.extend(result['errors'])
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Batch {batch_id} completed: {success_count} success, {error_count} errors in {processing_time:.2f}s")
            
            return BatchResult(
                batch_id=batch_id,
                success_count=success_count,
                error_count=error_count,
                total_processed=len(logs),
                processing_time=processing_time,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"❌ Batch insert failed: {str(e)}")
            return BatchResult(
                batch_id=batch_id,
                success_count=0,
                error_count=len(logs),
                total_processed=len(logs),
                processing_time=time.time() - start_time,
                errors=[str(e)]
            )
    
    async def _process_insert_chunk(self, chunk: ProcessingChunk, semaphore: asyncio.Semaphore):
        """Process a single chunk of logs"""
        async with semaphore:
            try:
                if self.db_pool:
                    return await self._insert_chunk_to_db(chunk)
                else:
                    return await self._insert_chunk_to_memory(chunk)
            except Exception as e:
                logger.error(f"❌ Chunk {chunk.chunk_id} failed: {str(e)}")
                raise
    
    async def _insert_chunk_to_db(self, chunk: ProcessingChunk):
        """Insert chunk to PostgreSQL database"""
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                success_count = 0
                error_count = 0
                errors = []
                
                for log in chunk.logs:
                    try:
                        await conn.execute("""
                            INSERT INTO logs (id, timestamp, level, service, message, metadata, batch_id)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """, 
                        log.id, log.timestamp, log.level, 
                        log.service, log.message, 
                        json.dumps(log.metadata), chunk.chunk_id)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Log {log.id}: {str(e)}")
                
                return {
                    'success_count': success_count,
                    'error_count': error_count,
                    'errors': errors
                }
    
    async def _insert_chunk_to_memory(self, chunk: ProcessingChunk):
        """Insert chunk to in-memory storage (fallback)"""
        # Simulate database insert with delay
        await asyncio.sleep(0.1)
        
        success_count = len(chunk.logs)
        logger.info(f"💾 Inserted chunk {chunk.chunk_id}: {success_count} logs to memory")
        
        return {
            'success_count': success_count,
            'error_count': 0,
            'errors': []
        }
    
    def _create_chunks(self, logs: List[LogEntry], chunk_size: int, batch_id: str) -> List[ProcessingChunk]:
        """Split logs into processing chunks"""
        chunks = []
        
        for i in range(0, len(logs), chunk_size):
            chunk_logs = logs[i:i + chunk_size]
            chunk = ProcessingChunk(
                chunk_id=f"{batch_id}-{i//chunk_size}",
                logs=chunk_logs,
                start_index=i,
                end_index=min(i + chunk_size, len(logs))
            )
            chunks.append(chunk)
        
        return chunks
    
    async def process_batch_query(self, query_request: Dict[str, Any], db_session) -> QueryResult:
        """Process batch query operations"""
        start_time = time.time()
        
        # Simulate query processing
        await asyncio.sleep(0.05)  # Simulate query time
        
        # Return mock data for demonstration
        sample_logs = [
            LogEntry(
                id=f"query-{i}",
                timestamp=datetime.now(timezone.utc),
                level="INFO",
                service="batch-api",
                message=f"Sample log entry {i}",
                metadata={"query": "batch_operation"}
            )
            for i in range(50)  # Return 50 sample logs
        ]
        
        processing_time = time.time() - start_time
        
        return QueryResult(
            logs=sample_logs,
            total_count=len(sample_logs),
            processing_time=processing_time,
            query_stats={
                "execution_time": processing_time,
                "rows_scanned": 1000,
                "index_usage": "primary_key"
            }
        )
    
    async def process_batch_delete(self, delete_request: Dict[str, Any], db_session) -> BatchResult:
        """Process batch delete operations"""
        batch_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Simulate delete processing
        await asyncio.sleep(0.1)
        
        # Mock successful deletion
        total_processed = delete_request.get('count', 100)
        
        processing_time = time.time() - start_time
        
        return BatchResult(
            batch_id=batch_id,
            success_count=total_processed,
            error_count=0,
            total_processed=total_processed,
            processing_time=processing_time,
            errors=[]
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check batch processor health"""
        return {
            "status": "healthy",
            "database_pool": "connected" if self.db_pool else "disconnected",
            "max_chunk_size": self.max_chunk_size,
            "max_concurrent_chunks": self.max_concurrent_chunks
        }
EOF

# Create data models
echo "📋 Creating data models..."
cat > src/models/log_models.py << 'EOF'
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class LogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(..., description="Log level (INFO, WARN, ERROR, DEBUG)")
    service: str = Field(..., description="Service name that generated the log")
    message: str = Field(..., description="Log message content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class BatchRequest(BaseModel):
    logs: List[LogEntry] = Field(..., description="List of log entries to process")
    chunk_size: Optional[int] = Field(default=1000, description="Size of processing chunks")
    transaction_mode: Optional[str] = Field(default="optimistic", description="Transaction handling mode")

class BatchResponse(BaseModel):
    success: bool = Field(..., description="Overall batch operation success")
    total_processed: int = Field(..., description="Total number of items processed")
    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of failed operations")
    processing_time: float = Field(..., description="Total processing time in seconds")
    batch_id: str = Field(..., description="Unique batch identifier")
    errors: List[str] = Field(default_factory=list, description="List of error messages")

class BatchResult(BaseModel):
    batch_id: str
    success_count: int
    error_count: int
    total_processed: int
    processing_time: float
    errors: List[str] = Field(default_factory=list)

class QueryResult(BaseModel):
    logs: List[LogEntry]
    total_count: int
    processing_time: float
    query_stats: Dict[str, Any]

class BatchStats(BaseModel):
    total_batches_processed: int = 0
    total_logs_processed: int = 0
    average_batch_size: float = 0.0
    average_processing_time: float = 0.0
    success_rate: float = 0.0
    throughput_per_second: float = 0.0
    current_queue_size: int = 0
EOF

# Create metrics collector
echo "📊 Creating metrics collector..."
cat > src/monitoring/metrics.py << 'EOF'
import asyncio
import time
from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
import psutil
import threading

from ..models.log_models import BatchStats

@dataclass
class OperationMetric:
    operation_type: str
    timestamp: float
    batch_size: int
    processing_time: float
    success_count: int
    
@dataclass
class SystemMetrics:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_io: Dict[str, Any] = field(default_factory=dict)
    network_io: Dict[str, Any] = field(default_factory=dict)

class MetricsCollector:
    def __init__(self):
        self.operations: List[OperationMetric] = []
        self.system_metrics: SystemMetrics = SystemMetrics()
        self.collection_active = False
        self.lock = threading.Lock()
        
    def start_collection(self):
        """Start background metrics collection"""
        self.collection_active = True
        threading.Thread(target=self._collect_system_metrics, daemon=True).start()
        
    def stop_collection(self):
        """Stop metrics collection"""
        self.collection_active = False
        
    def _collect_system_metrics(self):
        """Background thread to collect system metrics"""
        while self.collection_active:
            try:
                self.system_metrics.cpu_percent = psutil.cpu_percent()
                self.system_metrics.memory_percent = psutil.virtual_memory().percent
                self.system_metrics.disk_io = psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
                self.system_metrics.network_io = psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
            except Exception as e:
                print(f"⚠️ Metrics collection error: {e}")
            
            time.sleep(5)  # Collect every 5 seconds
    
    async def record_batch_operation(
        self,
        operation_type: str,
        batch_size: int,
        processing_time: float,
        success_count: int
    ):
        """Record a batch operation metric"""
        with self.lock:
            metric = OperationMetric(
                operation_type=operation_type,
                timestamp=time.time(),
                batch_size=batch_size,
                processing_time=processing_time,
                success_count=success_count
            )
            self.operations.append(metric)
            
            # Keep only last 1000 operations
            if len(self.operations) > 1000:
                self.operations = self.operations[-1000:]
    
    async def get_batch_stats(self) -> BatchStats:
        """Get aggregated batch statistics"""
        with self.lock:
            if not self.operations:
                return BatchStats()
            
            total_batches = len(self.operations)
            total_logs = sum(op.batch_size for op in self.operations)
            total_processing_time = sum(op.processing_time for op in self.operations)
            total_success = sum(op.success_count for op in self.operations)
            
            # Calculate recent throughput (last 60 seconds)
            recent_time = time.time() - 60
            recent_ops = [op for op in self.operations if op.timestamp > recent_time]
            recent_logs = sum(op.success_count for op in recent_ops)
            
            return BatchStats(
                total_batches_processed=total_batches,
                total_logs_processed=total_logs,
                average_batch_size=total_logs / total_batches if total_batches > 0 else 0,
                average_processing_time=total_processing_time / total_batches if total_batches > 0 else 0,
                success_rate=(total_success / total_logs * 100) if total_logs > 0 else 0,
                throughput_per_second=recent_logs / 60 if recent_logs > 0 else 0,
                current_queue_size=0  # Would be actual queue size in production
            )
    
    async def get_current_stats(self) -> Dict[str, Any]:
        """Get current system and batch statistics"""
        batch_stats = await self.get_batch_stats()
        
        return {
            "batch_stats": batch_stats.dict(),
            "system_metrics": {
                "cpu_percent": self.system_metrics.cpu_percent,
                "memory_percent": self.system_metrics.memory_percent,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "recent_operations": [
                {
                    "type": op.operation_type,
                    "batch_size": op.batch_size,
                    "processing_time": op.processing_time,
                    "timestamp": op.timestamp
                }
                for op in self.operations[-10:]  # Last 10 operations
            ]
        }
    
    def is_healthy(self) -> bool:
        """Check if metrics collection is healthy"""
        return self.collection_active
EOF

# Create monitoring dashboard
echo "📊 Creating monitoring dashboard..."
cat > src/monitoring/dashboard.py << 'EOF'
import asyncio
import aiohttp
from aiohttp import web, WSMsgType
import json
import time

class MonitoringDashboard:
    def __init__(self):
        self.app = web.Application()
        self.websockets = set()
        self.setup_routes()
        
    def setup_routes(self):
        self.app.router.add_get('/', self.dashboard_handler)
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_static('/static', 'static', name='static')
        
    async def dashboard_handler(self, request):
        """Serve the monitoring dashboard"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Batch API Operations Monitor</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metric-value { font-size: 24px; font-weight: bold; color: #2563eb; }
                .metric-label { color: #6b7280; margin-top: 5px; }
                .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
                .status-healthy { background-color: #10b981; }
                .status-warning { background-color: #f59e0b; }
                .operations-list { max-height: 400px; overflow-y: auto; }
                .operation-item { padding: 8px; border-bottom: 1px solid #e5e7eb; font-family: monospace; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Batch API Operations Monitor</h1>
                    <p><span class="status-indicator status-healthy"></span>System Status: <span id="system-status">Healthy</span></p>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value" id="total-batches">0</div>
                        <div class="metric-label">Total Batches Processed</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-value" id="total-logs">0</div>
                        <div class="metric-label">Total Logs Processed</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-value" id="throughput">0.0</div>
                        <div class="metric-label">Throughput (logs/sec)</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-value" id="success-rate">0%</div>
                        <div class="metric-label">Success Rate</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-value" id="avg-batch-size">0</div>
                        <div class="metric-label">Average Batch Size</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-value" id="avg-processing-time">0.0s</div>
                        <div class="metric-label">Average Processing Time</div>
                    </div>
                </div>
                
                <div class="metric-card" style="margin-top: 20px;">
                    <h3>Recent Operations</h3>
                    <div id="operations-list" class="operations-list">
                        <div class="operation-item">Waiting for operations...</div>
                    </div>
                </div>
            </div>
            
            <script>
                const ws = new WebSocket('ws://localhost:8001/ws');
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    updateDashboard(data);
                };
                
                function updateDashboard(data) {
                    const stats = data.batch_stats;
                    const systemMetrics = data.system_metrics;
                    
                    document.getElementById('total-batches').textContent = stats.total_batches_processed;
                    document.getElementById('total-logs').textContent = stats.total_logs_processed.toLocaleString();
                    document.getElementById('throughput').textContent = stats.throughput_per_second.toFixed(1);
                    document.getElementById('success-rate').textContent = stats.success_rate.toFixed(1) + '%';
                    document.getElementById('avg-batch-size').textContent = Math.round(stats.average_batch_size);
                    document.getElementById('avg-processing-time').textContent = stats.average_processing_time.toFixed(3) + 's';
                    
                    // Update recent operations
                    const operationsList = document.getElementById('operations-list');
                    if (data.recent_operations && data.recent_operations.length > 0) {
                        operationsList.innerHTML = data.recent_operations.map(op => 
                            `<div class="operation-item">
                                ${new Date(op.timestamp * 1000).toLocaleTimeString()} - 
                                ${op.type.toUpperCase()}: ${op.batch_size} logs in ${op.processing_time.toFixed(3)}s
                            </div>`
                        ).join('');
                    }
                }
                
                // Connection status
                ws.onopen = function() {
                    document.getElementById('system-status').textContent = 'Connected';
                };
                
                ws.onclose = function() {
                    document.getElementById('system-status').textContent = 'Disconnected';
                };
            </script>
        </body>
        </html>
        """
        return web.Response(text=html_content, content_type='text/html')
    
    async def websocket_handler(self, request):
        """Handle WebSocket connections for real-time updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.add(ws)
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    if msg.data == 'close':
                        await ws.close()
                elif msg.type == WSMsgType.ERROR:
                    print(f'WebSocket error: {ws.exception()}')
        finally:
            self.websockets.discard(ws)
            
        return ws
    
    async def broadcast_metrics(self, metrics_data):
        """Broadcast metrics to all connected WebSockets"""
        if self.websockets:
            message = json.dumps(metrics_data)
            await asyncio.gather(
                *[ws.send_str(message) for ws in self.websockets.copy()],
                return_exceptions=True
            )
    
    async def start_metrics_broadcast(self):
        """Start periodic metrics broadcasting"""
        while True:
            try:
                # Fetch metrics from main API
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://localhost:8000/api/v1/metrics/batch') as resp:
                        if resp.status == 200:
                            batch_stats = await resp.json()
                            
                            # Get current stats
                            async with session.get('http://localhost:8000/api/v1/health') as health_resp:
                                health_data = await health_resp.json() if health_resp.status == 200 else {}
                            
                            metrics_data = {
                                'batch_stats': batch_stats,
                                'system_metrics': {'cpu_percent': 0, 'memory_percent': 0},
                                'recent_operations': []
                            }
                            
                            await self.broadcast_metrics(metrics_data)
            except Exception as e:
                print(f"⚠️ Metrics broadcast error: {e}")
            
            await asyncio.sleep(2)  # Update every 2 seconds

async def run_dashboard():
    """Run the monitoring dashboard"""
    dashboard = MonitoringDashboard()
    
    # Start metrics broadcasting
    asyncio.create_task(dashboard.start_metrics_broadcast())
    
    # Start web server
    runner = web.AppRunner(dashboard.app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8001)
    await site.start()
    
    print("📊 Monitoring Dashboard running on http://localhost:8001")
    
    # Keep running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_dashboard())
EOF

# Create database utilities
echo "🗄️ Creating database utilities..."
cat > src/utils/database_setup.py << 'EOF'
import asyncpg
import asyncio
import logging

logger = logging.getLogger(__name__)

async def create_database_schema():
    """Create database schema for log storage"""
    try:
        # Try to connect to PostgreSQL
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='postgres'
        )
        
        # Create database if it doesn't exist
        await conn.execute("CREATE DATABASE logdb")
        await conn.close()
        
        # Connect to the new database
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='logdb'
        )
        
        # Create logs table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id UUID PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                level VARCHAR(10) NOT NULL,
                service VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                metadata JSONB DEFAULT '{}',
                batch_id VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                INDEX BTREE (timestamp),
                INDEX BTREE (level),
                INDEX BTREE (service),
                INDEX BTREE (batch_id)
            )
        """)
        
        await conn.close()
        logger.info("✅ Database schema created successfully")
        
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL setup failed: {e}")
        logger.info("📝 System will use in-memory storage for demonstration")

if __name__ == "__main__":
    asyncio.run(create_database_schema())
EOF

cat > src/utils/database.py << 'EOF'
import asyncpg
from typing import Optional

_db_pool: Optional[asyncpg.Pool] = None

async def get_db_pool():
    """Get database connection pool"""
    global _db_pool
    if _db_pool is None:
        try:
            _db_pool = await asyncpg.create_pool(
                host='localhost',
                port=5432,
                user='postgres',
                password='postgres',
                database='logdb',
                min_size=2,
                max_size=10
            )
        except Exception:
            _db_pool = None
    return _db_pool

async def get_db_session():
    """Get database session (dependency)"""
    pool = await get_db_pool()
    if pool:
        async with pool.acquire() as conn:
            yield conn
    else:
        yield None  # In-memory fallback
EOF

# Create demonstration script
echo "🎬 Creating demonstration script..."
cat > src/utils/demo.py << 'EOF'
import asyncio
import aiohttp
import json
import time
import random
from datetime import datetime, timezone

async def generate_sample_logs(count: int = 1000):
    """Generate sample log entries for testing"""
    services = ['user-service', 'payment-service', 'inventory-service', 'notification-service']
    levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
    
    logs = []
    for i in range(count):
        log = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': random.choice(levels),
            'service': random.choice(services),
            'message': f'Sample log message {i} - {random.choice(["Operation completed", "Processing request", "Cache updated", "Database query executed"])}',
            'metadata': {
                'request_id': f'req_{random.randint(1000, 9999)}',
                'user_id': f'user_{random.randint(1, 1000)}',
                'duration_ms': random.randint(10, 500)
            }
        }
        logs.append(log)
    
    return logs

async def run_batch_demo():
    """Run comprehensive batch operations demonstration"""
    print("🎬 Starting Batch API Operations Demonstration")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Wait for API to be ready
    print("⏳ Waiting for API to be ready...")
    for _ in range(30):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/api/v1/health") as resp:
                    if resp.status == 200:
                        print("✅ API is ready!")
                        break
        except:
            pass
        await asyncio.sleep(1)
    else:
        print("❌ API not ready, continuing with demo anyway...")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Small batch insert
        print("\n🧪 Test 1: Small Batch Insert (100 logs)")
        logs = await generate_sample_logs(100)
        batch_request = {
            'logs': logs,
            'chunk_size': 50
        }
        
        start_time = time.time()
        try:
            async with session.post(
                f"{base_url}/api/v1/logs/batch",
                json=batch_request
            ) as resp:
                result = await resp.json()
                end_time = time.time()
                
                print(f"✅ Status: {result['success']}")
                print(f"📊 Processed: {result['total_processed']} logs")
                print(f"✅ Success: {result['success_count']}")
                print(f"❌ Errors: {result['error_count']}")
                print(f"⏱️ Time: {end_time - start_time:.2f}s (API: {result['processing_time']:.3f}s)")
        except Exception as e:
            print(f"❌ Test 1 failed: {e}")
        
        # Test 2: Large batch insert  
        print("\n🧪 Test 2: Large Batch Insert (5000 logs)")
        logs = await generate_sample_logs(5000)
        batch_request = {
            'logs': logs,
            'chunk_size': 1000
        }
        
        start_time = time.time()
        try:
            async with session.post(
                f"{base_url}/api/v1/logs/batch",
                json=batch_request
            ) as resp:
                result = await resp.json()
                end_time = time.time()
                
                print(f"✅ Status: {result['success']}")
                print(f"📊 Processed: {result['total_processed']} logs")
                print(f"✅ Success: {result['success_count']}")
                print(f"❌ Errors: {result['error_count']}")
                print(f"⏱️ Time: {end_time - start_time:.2f}s (API: {result['processing_time']:.3f}s)")
                print(f"🚀 Throughput: {result['success_count'] / result['processing_time']:.0f} logs/sec")
        except Exception as e:
            print(f"❌ Test 2 failed: {e}")
        
        # Test 3: Batch query
        print("\n🧪 Test 3: Batch Query Operation")
        query_request = {
            'filters': {
                'level': 'ERROR',
                'service': 'payment-service'
            },
            'limit': 100
        }
        
        try:
            async with session.post(
                f"{base_url}/api/v1/logs/batch/query",
                json=query_request
            ) as resp:
                result = await resp.json()
                
                print(f"✅ Status: {result['success']}")
                print(f"📊 Results: {result['total_results']} logs")
                print(f"⏱️ Time: {result['processing_time']:.3f}s")
                print(f"📈 Query Stats: {result['query_stats']}")
        except Exception as e:
            print(f"❌ Test 3 failed: {e}")
        
        # Test 4: Performance comparison
        print("\n🧪 Test 4: Performance Comparison (Individual vs Batch)")
        
        # Individual operations (simulated)
        individual_time = 100 * 0.01  # 100 logs × 10ms each = 1s
        print(f"📈 Individual operations (100 logs): ~{individual_time:.1f}s")
        
        # Batch operation
        logs = await generate_sample_logs(100)
        batch_request = {'logs': logs, 'chunk_size': 100}
        
        start_time = time.time()
        try:
            async with session.post(
                f"{base_url}/api/v1/logs/batch",
                json=batch_request
            ) as resp:
                result = await resp.json()
                batch_time = time.time() - start_time
                
                improvement = individual_time / batch_time if batch_time > 0 else 0
                print(f"🚀 Batch operation (100 logs): {batch_time:.2f}s")
                print(f"⚡ Performance improvement: {improvement:.1f}x faster")
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
        
        # Test 5: Get metrics
        print("\n🧪 Test 5: Current System Metrics")
        try:
            async with session.get(f"{base_url}/api/v1/metrics/batch") as resp:
                metrics = await resp.json()
                
                print(f"📊 Total Batches: {metrics['total_batches_processed']}")
                print(f"📊 Total Logs: {metrics['total_logs_processed']}")
                print(f"📊 Average Batch Size: {metrics['average_batch_size']:.1f}")
                print(f"📊 Success Rate: {metrics['success_rate']:.1f}%")
                print(f"🚀 Throughput: {metrics['throughput_per_second']:.1f} logs/sec")
        except Exception as e:
            print(f"❌ Metrics test failed: {e}")
    
    print("\n🎉 Batch API Demonstration Completed!")
    print("🌐 Open http://localhost:8000/docs for interactive API documentation")
    print("📊 Open http://localhost:8001 for real-time monitoring dashboard")

if __name__ == "__main__":
    asyncio.run(run_batch_demo())
EOF

# Create package init files
echo "📦 Creating package structure..."
touch src/__init__.py
touch src/api/__init__.py
touch src/batch/__init__.py
touch src/models/__init__.py
touch src/utils/__init__.py
touch src/monitoring/__init__.py

# Create main dashboard template
mkdir -p templates
cat > templates/dashboard.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Batch API Operations Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f8fafc; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; text-align: center; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border-left: 4px solid #3b82f6; }
        .metric-value { font-size: 32px; font-weight: bold; color: #1f2937; margin-bottom: 5px; }
        .metric-label { color: #6b7280; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }
        .chart-container { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); }
        .api-demo { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); margin-top: 20px; }
        .demo-button { background: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; margin: 5px; font-size: 14px; }
        .demo-button:hover { background: #2563eb; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; background: #10b981; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Batch API Operations Dashboard</h1>
            <p><span class="status-indicator"></span>System Status: Operational</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{{ stats.batch_stats.total_batches_processed or 0 }}</div>
                <div class="metric-label">Total Batches</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value">{{ (stats.batch_stats.total_logs_processed or 0) | int }}</div>
                <div class="metric-label">Total Logs</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f" | format(stats.batch_stats.throughput_per_second or 0) }}</div>
                <div class="metric-label">Logs/Second</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f%" | format(stats.batch_stats.success_rate or 0) }}</div>
                <div class="metric-label">Success Rate</div>
            </div>
        </div>
        
        <div class="api-demo">
            <h3>🧪 API Testing Interface</h3>
            <p>Test batch operations directly from this dashboard:</p>
            <button class="demo-button" onclick="testSmallBatch()">Test Small Batch (100 logs)</button>
            <button class="demo-button" onclick="testLargeBatch()">Test Large Batch (1000 logs)</button>
            <button class="demo-button" onclick="testQuery()">Test Batch Query</button>
            <button class="demo-button" onclick="viewDocs()">View API Docs</button>
            
            <div id="test-results" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; font-family: monospace; white-space: pre-wrap; display: none;"></div>
        </div>
    </div>
    
    <script>
        async function testSmallBatch() {
            showLoading();
            try {
                const logs = generateSampleLogs(100);
                const response = await fetch('/api/v1/logs/batch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({logs: logs, chunk_size: 50})
                });
                const result = await response.json();
                showResult(`Small Batch Test Results:\n${JSON.stringify(result, null, 2)}`);
            } catch (error) {
                showResult(`Error: ${error.message}`);
            }
        }
        
        async function testLargeBatch() {
            showLoading();
            try {
                const logs = generateSampleLogs(1000);
                const response = await fetch('/api/v1/logs/batch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({logs: logs, chunk_size: 200})
                });
                const result = await response.json();
                showResult(`Large Batch Test Results:\n${JSON.stringify(result, null, 2)}`);
            } catch (error) {
                showResult(`Error: ${error.message}`);
            }
        }
        
        async function testQuery() {
            showLoading();
            try {
                const response = await fetch('/api/v1/logs/batch/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        filters: {level: 'INFO', service: 'user-service'},
                        limit: 50
                    })
                });
                const result = await response.json();
                showResult(`Batch Query Results:\n${JSON.stringify(result, null, 2)}`);
            } catch (error) {
                showResult(`Error: ${error.message}`);
            }
        }
        
        function viewDocs() {
            window.open('/docs', '_blank');
        }
        
        function generateSampleLogs(count) {
            const services = ['user-service', 'payment-service', 'inventory-service'];
            const levels = ['INFO', 'WARN', 'ERROR', 'DEBUG'];
            const logs = [];
            
            for (let i = 0; i < count; i++) {
                logs.push({
                    timestamp: new Date().toISOString(),
                    level: levels[Math.floor(Math.random() * levels.length)],
                    service: services[Math.floor(Math.random() * services.length)],
                    message: `Sample log message ${i}`,
                    metadata: {
                        request_id: `req_${Math.floor(Math.random() * 10000)}`,
                        user_id: `user_${Math.floor(Math.random() * 1000)}`
                    }
                });
            }
            return logs;
        }
        
        function showLoading() {
            const results = document.getElementById('test-results');
            results.style.display = 'block';
            results.textContent = 'Loading...';
        }
        
        function showResult(text) {
            const results = document.getElementById('test-results');
            results.style.display = 'block';
            results.textContent = text;
        }
        
        // Auto-refresh page every 30 seconds
        setInterval(() => {
            window.location.reload();
        }, 30000);
    </script>
</body>
</html>
EOF

# Create test files
echo "🧪 Creating test files..."
cat > tests/unit/test_batch_processor.py << 'EOF'
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone

from src.batch.batch_processor import BatchProcessor
from src.models.log_models import LogEntry

@pytest.fixture
def sample_logs():
    return [
        LogEntry(
            id=f"test-{i}",
            timestamp=datetime.now(timezone.utc),
            level="INFO",
            service="test-service",
            message=f"Test message {i}",
            metadata={"test": True}
        )
        for i in range(100)
    ]

@pytest.fixture
def batch_processor():
    processor = BatchProcessor()
    processor.db_pool = None  # Use in-memory mode for testing
    return processor

@pytest.mark.asyncio
async def test_batch_insert_success(batch_processor, sample_logs):
    """Test successful batch insert"""
    result = await batch_processor.process_batch_insert(
        sample_logs, 
        None, 
        chunk_size=50
    )
    
    assert result.success_count == 100
    assert result.error_count == 0
    assert result.total_processed == 100
    assert result.processing_time > 0

@pytest.mark.asyncio
async def test_batch_insert_chunking(batch_processor, sample_logs):
    """Test batch chunking logic"""
    chunks = batch_processor._create_chunks(sample_logs, 30, "test-batch")
    
    assert len(chunks) == 4  # 100 logs / 30 = 3.33, rounded up to 4
    assert chunks[0].start_index == 0
    assert chunks[0].end_index == 30
    assert chunks[-1].start_index == 90
    assert chunks[-1].end_index == 100

@pytest.mark.asyncio
async def test_health_check(batch_processor):
    """Test health check functionality"""
    health = await batch_processor.health_check()
    
    assert health["status"] == "healthy"
    assert "max_chunk_size" in health
    assert "max_concurrent_chunks" in health

def test_chunk_creation_edge_cases(batch_processor):
    """Test chunk creation with edge cases"""
    # Empty logs
    chunks = batch_processor._create_chunks([], 100, "empty-batch")
    assert len(chunks) == 0
    
    # Single log
    single_log = [LogEntry(
        level="INFO",
        service="test",
        message="single"
    )]
    chunks = batch_processor._create_chunks(single_log, 100, "single-batch")
    assert len(chunks) == 1
    assert len(chunks[0].logs) == 1
EOF

cat > tests/integration/test_api_endpoints.py << 'EOF'
import pytest
import asyncio
from fastapi.testclient import TestClient
import json

from src.api.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data

def test_batch_insert_endpoint():
    """Test batch insert API endpoint"""
    logs = [
        {
            "timestamp": "2025-06-01T10:00:00Z",
            "level": "INFO",
            "service": "test-service",
            "message": f"Test message {i}",
            "metadata": {"test": True}
        }
        for i in range(10)
    ]
    
    response = client.post("/api/v1/logs/batch", json={
        "logs": logs,
        "chunk_size": 5
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["total_processed"] == 10
    assert data["success_count"] == 10
    assert data["error_count"] == 0

def test_batch_insert_validation():
    """Test batch insert input validation"""
    # Test empty batch
    response = client.post("/api/v1/logs/batch", json={"logs": []})
    assert response.status_code == 200  # Empty batch should succeed
    
    # Test oversized batch
    large_logs = [
        {
            "level": "INFO",
            "service": "test",
            "message": f"message {i}"
        }
        for i in range(15000)  # Exceeds 10000 limit
    ]
    
    response = client.post("/api/v1/logs/batch", json={"logs": large_logs})
    assert response.status_code == 400

def test_batch_query_endpoint():
    """Test batch query API endpoint"""
    query_request = {
        "filters": {
            "level": "ERROR",
            "service": "payment-service"
        },
        "limit": 50
    }
    
    response = client.post("/api/v1/logs/batch/query", json=query_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] == True
    assert "total_results" in data
    assert "logs" in data
    assert "processing_time" in data

def test_metrics_endpoint():
    """Test metrics API endpoint"""
    response = client.get("/api/v1/metrics/batch")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_batches_processed" in data
    assert "total_logs_processed" in data
    assert "average_batch_size" in data
    assert "success_rate" in data
EOF

cat > tests/performance/test_performance.py << 'EOF'
import pytest
import asyncio
import time
import statistics
from src.batch.batch_processor import BatchProcessor
from src.models.log_models import LogEntry
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_throughput_performance():
    """Test batch processing throughput"""
    processor = BatchProcessor()
    processor.db_pool = None  # Use in-memory mode
    
    # Generate test data
    log_counts = [100, 500, 1000, 2000]
    throughput_results = []
    
    for count in log_counts:
        logs = [
            LogEntry(
                timestamp=datetime.now(timezone.utc),
                level="INFO",
                service=f"service-{i % 5}",
                message=f"Performance test message {i}"
            )
            for i in range(count)
        ]
        
        start_time = time.time()
        result = await processor.process_batch_insert(logs, None, chunk_size=500)
        end_time = time.time()
        
        processing_time = end_time - start_time
        throughput = count / processing_time
        throughput_results.append(throughput)
        
        print(f"📊 {count} logs: {throughput:.0f} logs/sec")
        
        # Assert minimum throughput expectations
        assert throughput > 100  # At least 100 logs/sec
        assert result.success_count == count

    # Test throughput consistency
    assert max(throughput_results) / min(throughput_results) < 3  # Within 3x variance

@pytest.mark.asyncio 
async def test_chunk_size_optimization():
    """Test optimal chunk size for performance"""
    processor = BatchProcessor()
    processor.db_pool = None
    
    logs = [
        LogEntry(
            level="INFO",
            service="perf-test",
            message=f"Chunk optimization test {i}"
        )
        for i in range(1000)
    ]
    
    chunk_sizes = [100, 250, 500, 1000]
    performance_data = []
    
    for chunk_size in chunk_sizes:
        start_time = time.time()
        result = await processor.process_batch_insert(logs, None, chunk_size=chunk_size)
        processing_time = time.time() - start_time
        
        performance_data.append({
            'chunk_size': chunk_size,
            'processing_time': processing_time,
            'throughput': 1000 / processing_time
        })
        
        print(f"📈 Chunk size {chunk_size}: {processing_time:.3f}s ({1000/processing_time:.0f} logs/sec)")
    
    # Verify all chunk sizes complete successfully
    for data in performance_data:
        assert data['throughput'] > 50  # Minimum acceptable throughput

@pytest.mark.asyncio
async def test_concurrent_batch_processing():
    """Test concurrent batch processing performance"""
    processor = BatchProcessor()
    processor.db_pool = None
    
    # Create multiple batches for concurrent processing
    batches = []
    for batch_num in range(5):
        batch = [
            LogEntry(
                level="INFO",
                service=f"concurrent-service-{batch_num}",
                message=f"Concurrent test batch {batch_num} message {i}"
            )
            for i in range(200)
        ]
        batches.append(batch)
    
    # Process batches concurrently
    start_time = time.time()
    tasks = [
        processor.process_batch_insert(batch, None, chunk_size=100)
        for batch in batches
    ]
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    total_processing_time = end_time - start_time
    total_logs = sum(len(batch) for batch in batches)
    concurrent_throughput = total_logs / total_processing_time
    
    print(f"🔄 Concurrent processing: {concurrent_throughput:.0f} logs/sec across {len(batches)} batches")
    
    # Verify all batches completed successfully
    for result in results:
        assert result.success_count == 200
        assert result.error_count == 0
    
    # Concurrent processing should be faster than sequential
    assert concurrent_throughput > 200  # Should achieve good concurrent throughput
EOF

# Create Docker configuration
echo "🐳 Creating Docker configuration..."
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/

# Create necessary directories
RUN mkdir -p logs tests config

# Expose ports
EXPOSE 8000 8001

# Default command
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: logdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  batch-api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/logdb
      REDIS_URL: redis://redis:6379/0
    volumes:
      - .:/app

volumes:
  postgres_data:
EOF

cat > .dockerignore << 'EOF'
.git
.gitignore
README.md
Dockerfile
.dockerignore
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.pytest_cache/
.coverage
htmlcov/
.tox/
.env
.venv
EOF

# Create static files
mkdir -p static/{css,js}
echo "/* Batch API Styles */" > static/css/dashboard.css
echo "// Batch API Scripts" > static/js/dashboard.js

# Create configuration
cat > config/settings.py << 'EOF'
import os

class Settings:
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/logdb')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', '10000'))
    DEFAULT_CHUNK_SIZE = int(os.getenv('DEFAULT_CHUNK_SIZE', '1000'))
    MAX_CONCURRENT_CHUNKS = int(os.getenv('MAX_CONCURRENT_CHUNKS', '10'))

settings = Settings()
EOF

echo "✅ Project structure created successfully!"
echo ""
echo "📁 Project Structure:"
find . -type f -name "*.py" | head -20 | sed 's/^/  /'
echo "   ... and more files"

echo ""
echo "🚀 To start the system:"
echo "  ./start.sh"
echo ""
echo "🛑 To stop the system:"
echo "  ./stop.sh"
echo ""
echo "🧪 To run tests:"
echo "  source venv/bin/activate"
echo "  python -m pytest tests/ -v"
echo ""
echo "🐳 To run with Docker:"
echo "  docker-compose up --build"

# Make scripts executable
chmod +x start.sh stop.sh

echo ""
echo "✅ Day 91 Batch API Operations system is ready!"
echo "📚 Next: Run ./start.sh to start the system and see the demonstration"