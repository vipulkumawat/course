#!/bin/bash

# Day 74: Storage Format Optimization - Complete Implementation Script
# 254-Day Hands-On System Design Series

set -e

echo "🚀 Day 74: Setting up Storage Format Optimization System"
echo "====================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Create project structure
print_info "Creating project structure..."
mkdir -p storage-optimizer/{src/{storage,analyzer,web,utils},tests,config,data/{raw,optimized},logs,docker}

cd storage-optimizer

# Create requirements.txt with latest May 2025 libraries
cat > requirements.txt << 'EOF'
fastapi==0.111.0
uvicorn==0.30.1
pydantic==2.7.1
numpy==1.26.4
pandas==2.2.2
pyarrow==16.0.0
sqlite3
aiofiles==23.2.1
jinja2==3.1.4
websockets==12.0
pytest==8.2.0
pytest-asyncio==0.23.7
structlog==24.1.0
plotly==5.20.0
lz4==4.3.3
msgpack==1.0.8
psutil==5.9.8
EOF

print_status "Project structure created"

# Create main storage engine
cat > src/storage/storage_engine.py << 'EOF'
"""
Adaptive Storage Engine with Multiple Format Support
Automatically optimizes storage format based on access patterns
"""
import json
import struct
import lz4.frame
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio
import threading
from dataclasses import dataclass
from enum import Enum

class StorageFormat(Enum):
    ROW_ORIENTED = "row"
    COLUMNAR = "columnar"
    HYBRID = "hybrid"

@dataclass
class StorageMetrics:
    read_count: int = 0
    write_count: int = 0
    compression_ratio: float = 0.0
    query_time_avg: float = 0.0
    storage_size: int = 0

class AdaptiveStorageEngine:
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Storage backends
        self.row_storage = RowStorage(self.base_path / "row")
        self.columnar_storage = ColumnarStorage(self.base_path / "columnar")
        self.hybrid_storage = HybridStorage(self.base_path / "hybrid")
        
        # Pattern analyzer
        self.pattern_analyzer = QueryPatternAnalyzer()
        self.format_selector = FormatSelector()
        
        # Metrics tracking
        self.metrics = {}
        self.access_patterns = {}
        
        print("🏗️  Adaptive Storage Engine initialized")
    
    async def write_logs(self, logs: List[Dict[str, Any]], partition_key: str = "default") -> bool:
        """Write logs using optimal format based on current patterns"""
        try:
            # Analyze patterns to determine format
            optimal_format = await self.format_selector.select_format(
                partition_key, 
                self.access_patterns.get(partition_key, {})
            )
            
            # Route to appropriate storage backend
            if optimal_format == StorageFormat.ROW_ORIENTED:
                result = await self.row_storage.write(logs, partition_key)
            elif optimal_format == StorageFormat.COLUMNAR:
                result = await self.columnar_storage.write(logs, partition_key)
            else:  # HYBRID
                result = await self.hybrid_storage.write(logs, partition_key)
            
            # Update metrics
            self._update_write_metrics(partition_key, len(logs))
            
            print(f"📝 Written {len(logs)} logs using {optimal_format.value} format")
            return result
            
        except Exception as e:
            print(f"❌ Write error: {e}")
            return False
    
    async def read_logs(self, query: Dict[str, Any], partition_key: str = "default") -> List[Dict[str, Any]]:
        """Read logs using optimal storage backend"""
        start_time = datetime.now()
        
        try:
            # Track query pattern
            await self.pattern_analyzer.analyze_query(query, partition_key)
            
            # Determine which storage has the data
            format_used = self._determine_storage_location(partition_key)
            
            if format_used == StorageFormat.ROW_ORIENTED:
                results = await self.row_storage.read(query, partition_key)
            elif format_used == StorageFormat.COLUMNAR:
                results = await self.columnar_storage.read(query, partition_key)
            else:  # HYBRID
                results = await self.hybrid_storage.read(query, partition_key)
            
            # Update metrics
            query_time = (datetime.now() - start_time).total_seconds()
            self._update_read_metrics(partition_key, query_time)
            
            print(f"📖 Read {len(results)} logs in {query_time:.3f}s using {format_used.value} format")
            return results
            
        except Exception as e:
            print(f"❌ Read error: {e}")
            return []
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get storage optimization statistics"""
        stats = {
            'partitions': {},
            'total_storage_mb': 0,
            'compression_savings': 0,
            'format_distribution': {'row': 0, 'columnar': 0, 'hybrid': 0}
        }
        
        # Calculate stats for each partition
        for partition_key, metrics in self.metrics.items():
            stats['partitions'][partition_key] = {
                'reads': metrics.read_count,
                'writes': metrics.write_count,
                'avg_query_time': metrics.query_time_avg,
                'compression_ratio': metrics.compression_ratio,
                'storage_mb': round(metrics.storage_size / (1024 * 1024), 2)
            }
            stats['total_storage_mb'] += stats['partitions'][partition_key]['storage_mb']
        
        return stats
    
    def _update_write_metrics(self, partition_key: str, log_count: int):
        """Update write metrics for partition"""
        if partition_key not in self.metrics:
            self.metrics[partition_key] = StorageMetrics()
        
        self.metrics[partition_key].write_count += log_count
    
    def _update_read_metrics(self, partition_key: str, query_time: float):
        """Update read metrics for partition"""
        if partition_key not in self.metrics:
            self.metrics[partition_key] = StorageMetrics()
        
        metrics = self.metrics[partition_key]
        metrics.read_count += 1
        
        # Calculate moving average
        if metrics.read_count == 1:
            metrics.query_time_avg = query_time
        else:
            metrics.query_time_avg = (metrics.query_time_avg * (metrics.read_count - 1) + query_time) / metrics.read_count
    
    def _determine_storage_location(self, partition_key: str) -> StorageFormat:
        """Determine which storage backend contains the data"""
        # For demo, we'll check all backends and return the first with data
        if (self.base_path / "row" / f"{partition_key}.json").exists():
            return StorageFormat.ROW_ORIENTED
        elif (self.base_path / "columnar" / f"{partition_key}.parquet").exists():
            return StorageFormat.COLUMNAR
        else:
            return StorageFormat.HYBRID

class RowStorage:
    """Row-oriented storage optimized for full record access"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(exist_ok=True)
    
    async def write(self, logs: List[Dict[str, Any]], partition_key: str) -> bool:
        """Write logs in row-oriented format with compression"""
        try:
            file_path = self.base_path / f"{partition_key}.json"
            
            # Load existing data if file exists
            existing_logs = []
            if file_path.exists():
                with open(file_path, 'r') as f:
                    existing_logs = json.load(f)
            
            # Append new logs
            all_logs = existing_logs + logs
            
            # Write with LZ4 compression for speed
            compressed_data = lz4.frame.compress(
                json.dumps(all_logs, separators=(',', ':')).encode()
            )
            
            with open(f"{file_path}.lz4", 'wb') as f:
                f.write(compressed_data)
            
            # Also keep uncompressed for compatibility
            with open(file_path, 'w') as f:
                json.dump(all_logs, f, separators=(',', ':'))
            
            return True
        except Exception as e:
            print(f"❌ Row storage write error: {e}")
            return False
    
    async def read(self, query: Dict[str, Any], partition_key: str) -> List[Dict[str, Any]]:
        """Read logs from row-oriented storage"""
        try:
            file_path = self.base_path / f"{partition_key}.json"
            
            if not file_path.exists():
                return []
            
            # Try compressed version first
            compressed_path = f"{file_path}.lz4"
            if Path(compressed_path).exists():
                with open(compressed_path, 'rb') as f:
                    compressed_data = f.read()
                decompressed_data = lz4.frame.decompress(compressed_data)
                logs = json.loads(decompressed_data.decode())
            else:
                with open(file_path, 'r') as f:
                    logs = json.load(f)
            
            # Apply query filters
            filtered_logs = self._apply_filters(logs, query)
            return filtered_logs
            
        except Exception as e:
            print(f"❌ Row storage read error: {e}")
            return []
    
    def _apply_filters(self, logs: List[Dict], query: Dict) -> List[Dict]:
        """Apply query filters to logs"""
        filtered = logs
        
        if 'level' in query:
            filtered = [log for log in filtered if log.get('level') == query['level']]
        
        if 'service' in query:
            filtered = [log for log in filtered if log.get('service') == query['service']]
        
        if 'time_range' in query:
            start_time = query['time_range'].get('start')
            end_time = query['time_range'].get('end')
            if start_time:
                filtered = [log for log in filtered if log.get('timestamp', '') >= start_time]
            if end_time:
                filtered = [log for log in filtered if log.get('timestamp', '') <= end_time]
        
        return filtered

class ColumnarStorage:
    """Columnar storage optimized for analytical queries"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(exist_ok=True)
    
    async def write(self, logs: List[Dict[str, Any]], partition_key: str) -> bool:
        """Write logs in columnar format using Parquet"""
        try:
            file_path = self.base_path / f"{partition_key}.parquet"
            
            # Convert to DataFrame for columnar processing
            df = pd.DataFrame(logs)
            
            # Append to existing data if file exists
            if file_path.exists():
                existing_df = pd.read_parquet(file_path)
                df = pd.concat([existing_df, df], ignore_index=True)
            
            # Write as Parquet with compression
            df.to_parquet(
                file_path,
                compression='snappy',
                index=False
            )
            
            return True
        except Exception as e:
            print(f"❌ Columnar storage write error: {e}")
            return False
    
    async def read(self, query: Dict[str, Any], partition_key: str) -> List[Dict[str, Any]]:
        """Read logs from columnar storage with column pruning"""
        try:
            file_path = self.base_path / f"{partition_key}.parquet"
            
            if not file_path.exists():
                return []
            
            # Read with column pruning if specific columns requested
            columns = query.get('columns', None)
            df = pd.read_parquet(file_path, columns=columns)
            
            # Apply filters
            if 'level' in query:
                df = df[df['level'] == query['level']]
            
            if 'service' in query:
                df = df[df['service'] == query['service']]
            
            if 'time_range' in query:
                start_time = query['time_range'].get('start')
                end_time = query['time_range'].get('end')
                if start_time:
                    df = df[df['timestamp'] >= start_time]
                if end_time:
                    df = df[df['timestamp'] <= end_time]
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ Columnar storage read error: {e}")
            return []

class HybridStorage:
    """Hybrid storage that combines row and columnar approaches"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(exist_ok=True)
        
        # Use both storage types internally
        self.row_storage = RowStorage(self.base_path / "hot")
        self.columnar_storage = ColumnarStorage(self.base_path / "cold")
        
        # Hot data threshold (recent data stays in row format)
        self.hot_data_hours = 24
    
    async def write(self, logs: List[Dict[str, Any]], partition_key: str) -> bool:
        """Write to hot storage first, migrate to cold storage later"""
        return await self.row_storage.write(logs, partition_key)
    
    async def read(self, query: Dict[str, Any], partition_key: str) -> List[Dict[str, Any]]:
        """Read from both hot and cold storage, merge results"""
        try:
            hot_results = await self.row_storage.read(query, partition_key)
            cold_results = await self.columnar_storage.read(query, partition_key)
            
            # Merge and deduplicate results
            all_results = hot_results + cold_results
            
            # Remove duplicates based on log ID if available
            seen_ids = set()
            unique_results = []
            for result in all_results:
                log_id = result.get('id', str(hash(json.dumps(result, sort_keys=True))))
                if log_id not in seen_ids:
                    seen_ids.add(log_id)
                    unique_results.append(result)
            
            return unique_results
            
        except Exception as e:
            print(f"❌ Hybrid storage read error: {e}")
            return []

class QueryPatternAnalyzer:
    """Analyzes query patterns to inform storage format decisions"""
    
    def __init__(self):
        self.query_history = {}
        self.field_access_frequency = {}
    
    async def analyze_query(self, query: Dict[str, Any], partition_key: str):
        """Analyze query pattern and update statistics"""
        if partition_key not in self.query_history:
            self.query_history[partition_key] = []
            self.field_access_frequency[partition_key] = {}
        
        # Track query pattern
        query_pattern = {
            'timestamp': datetime.now().isoformat(),
            'query_type': self._classify_query(query),
            'fields_accessed': query.get('columns', []),
            'has_filters': bool(query.get('level') or query.get('service') or query.get('time_range'))
        }
        
        self.query_history[partition_key].append(query_pattern)
        
        # Update field access frequency
        for field in query_pattern['fields_accessed']:
            if field not in self.field_access_frequency[partition_key]:
                self.field_access_frequency[partition_key][field] = 0
            self.field_access_frequency[partition_key][field] += 1
        
        # Keep only recent history
        if len(self.query_history[partition_key]) > 1000:
            self.query_history[partition_key] = self.query_history[partition_key][-1000:]
    
    def _classify_query(self, query: Dict[str, Any]) -> str:
        """Classify query type for pattern analysis"""
        if query.get('columns') and len(query['columns']) <= 3:
            return 'analytical'  # Few columns = columnar friendly
        elif not query.get('columns'):
            return 'full_record'  # All columns = row friendly
        else:
            return 'mixed'  # Some columns = hybrid candidate

class FormatSelector:
    """Selects optimal storage format based on access patterns"""
    
    async def select_format(self, partition_key: str, access_patterns: Dict) -> StorageFormat:
        """Select optimal storage format based on patterns"""
        if not access_patterns:
            # Default to row-oriented for new partitions
            return StorageFormat.ROW_ORIENTED
        
        # Analyze patterns to make decision
        analytical_queries = access_patterns.get('analytical_queries', 0)
        full_record_queries = access_patterns.get('full_record_queries', 0)
        total_queries = analytical_queries + full_record_queries
        
        if total_queries == 0:
            return StorageFormat.ROW_ORIENTED
        
        analytical_ratio = analytical_queries / total_queries
        
        # Decision logic
        if analytical_ratio > 0.7:
            return StorageFormat.COLUMNAR
        elif analytical_ratio < 0.3:
            return StorageFormat.ROW_ORIENTED
        else:
            return StorageFormat.HYBRID
EOF

print_status "Storage engine implementation created"

# Create pattern analyzer
cat > src/analyzer/pattern_analyzer.py << 'EOF'
"""
Query Pattern Analyzer for Storage Format Optimization
"""
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json

class AccessPatternAnalyzer:
    def __init__(self):
        self.patterns = defaultdict(dict)
        self.field_statistics = defaultdict(lambda: defaultdict(int))
        self.query_performance = defaultdict(list)
        self.format_recommendations = {}
    
    def record_query(self, partition_key: str, query: Dict[str, Any], 
                    execution_time: float, result_count: int):
        """Record query execution for pattern analysis"""
        timestamp = datetime.now()
        
        query_record = {
            'timestamp': timestamp.isoformat(),
            'query': query,
            'execution_time': execution_time,
            'result_count': result_count,
            'query_type': self._classify_query_type(query)
        }
        
        # Store query performance
        if partition_key not in self.query_performance:
            self.query_performance[partition_key] = []
        
        self.query_performance[partition_key].append(query_record)
        
        # Update field access statistics
        self._update_field_stats(partition_key, query)
        
        # Clean old records (keep last 24 hours)
        self._cleanup_old_records(partition_key)
    
    def _classify_query_type(self, query: Dict[str, Any]) -> str:
        """Classify query type for optimization decisions"""
        columns = query.get('columns', [])
        has_aggregation = 'aggregation' in query
        has_full_scan = not query.get('filters', {})
        
        if has_aggregation and len(columns) <= 3:
            return 'analytical'
        elif not columns or len(columns) > 10:
            return 'full_record'
        elif has_full_scan:
            return 'scan_heavy'
        else:
            return 'mixed'
    
    def _update_field_stats(self, partition_key: str, query: Dict[str, Any]):
        """Update field access frequency statistics"""
        columns = query.get('columns', [])
        for column in columns:
            self.field_statistics[partition_key][column] += 1
    
    def _cleanup_old_records(self, partition_key: str):
        """Remove records older than 24 hours"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        if partition_key in self.query_performance:
            self.query_performance[partition_key] = [
                record for record in self.query_performance[partition_key]
                if datetime.fromisoformat(record['timestamp']) > cutoff_time
            ]
    
    def get_recommendations(self, partition_key: str) -> Dict[str, Any]:
        """Get storage format recommendations based on patterns"""
        if partition_key not in self.query_performance:
            return {'recommended_format': 'row_oriented', 'confidence': 'low'}
        
        records = self.query_performance[partition_key]
        
        if not records:
            return {'recommended_format': 'row_oriented', 'confidence': 'low'}
        
        # Analyze query types
        query_type_counts = defaultdict(int)
        total_queries = len(records)
        avg_execution_time = sum(r['execution_time'] for r in records) / total_queries
        
        for record in records:
            query_type_counts[record['query_type']] += 1
        
        # Calculate ratios
        analytical_ratio = query_type_counts['analytical'] / total_queries
        full_record_ratio = query_type_counts['full_record'] / total_queries
        
        # Make recommendation
        if analytical_ratio > 0.6:
            recommendation = 'columnar'
            confidence = 'high' if analytical_ratio > 0.8 else 'medium'
        elif full_record_ratio > 0.6:
            recommendation = 'row_oriented'
            confidence = 'high' if full_record_ratio > 0.8 else 'medium'
        else:
            recommendation = 'hybrid'
            confidence = 'medium'
        
        return {
            'recommended_format': recommendation,
            'confidence': confidence,
            'analytical_ratio': analytical_ratio,
            'full_record_ratio': full_record_ratio,
            'avg_execution_time': avg_execution_time,
            'total_queries': total_queries,
            'field_access_frequency': dict(self.field_statistics[partition_key])
        }
    
    def get_optimization_insights(self) -> Dict[str, Any]:
        """Get insights for storage optimization"""
        insights = {
            'partitions_analyzed': len(self.query_performance),
            'total_queries': sum(len(records) for records in self.query_performance.values()),
            'recommendations': {}
        }
        
        for partition_key in self.query_performance:
            insights['recommendations'][partition_key] = self.get_recommendations(partition_key)
        
        return insights
EOF

print_status "Pattern analyzer created"

# Create web dashboard
cat > src/web/dashboard.py << 'EOF'
"""
Storage Optimization Dashboard
Real-time monitoring and control interface
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime
import plotly.graph_objs as go
import plotly.utils

class StorageOptimizationDashboard:
    def __init__(self, storage_engine, pattern_analyzer):
        self.app = FastAPI(title="Storage Optimization Dashboard")
        self.storage_engine = storage_engine
        self.pattern_analyzer = pattern_analyzer
        self.templates = Jinja2Templates(directory="src/web/templates")
        self.active_connections: List[WebSocket] = []
        
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "title": "Storage Format Optimizer"
            })
        
        @self.app.get("/api/stats")
        async def get_stats():
            stats = self.storage_engine.get_optimization_stats()
            insights = self.pattern_analyzer.get_optimization_insights()
            
            return JSONResponse({
                "storage_stats": stats,
                "pattern_insights": insights,
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.get("/api/recommendations/{partition_key}")
        async def get_recommendations(partition_key: str):
            recommendations = self.pattern_analyzer.get_recommendations(partition_key)
            return JSONResponse(recommendations)
        
        @self.app.post("/api/optimize/{partition_key}")
        async def trigger_optimization(partition_key: str):
            # Trigger format optimization for partition
            try:
                # In real implementation, this would trigger migration
                result = {"status": "optimization_triggered", "partition": partition_key}
                await self.broadcast_update(result)
                return JSONResponse(result)
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.app.get("/api/performance-chart/{partition_key}")
        async def get_performance_chart(partition_key: str):
            # Generate performance chart data
            query_records = self.pattern_analyzer.query_performance.get(partition_key, [])
            
            if not query_records:
                return JSONResponse({"error": "No data available"})
            
            timestamps = [record['timestamp'] for record in query_records[-50:]]  # Last 50 queries
            execution_times = [record['execution_time'] for record in query_records[-50:]]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=execution_times,
                mode='lines+markers',
                name='Query Execution Time',
                line=dict(color='#4CAF50', width=2)
            ))
            
            fig.update_layout(
                title=f'Query Performance - {partition_key}',
                xaxis_title='Timestamp',
                yaxis_title='Execution Time (seconds)',
                template='plotly_white'
            )
            
            return JSONResponse(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    # Send periodic updates
                    stats = self.storage_engine.get_optimization_stats()
                    await websocket.send_text(json.dumps({
                        "type": "stats_update",
                        "data": stats,
                        "timestamp": datetime.now().isoformat()
                    }))
                    await asyncio.sleep(5)  # Update every 5 seconds
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
    
    async def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast updates to all connected websockets"""
        if self.active_connections:
            message = json.dumps({
                "type": "optimization_update",
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    self.active_connections.remove(connection)

# Template for dashboard HTML
dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Google Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .header h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }
        
        .card h3 {
            color: #4285f4;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        
        .metric:last-child { border-bottom: none; }
        
        .metric-value {
            font-weight: 600;
            color: #34a853;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-green { background-color: #34a853; }
        .status-yellow { background-color: #fbbc05; }
        .status-red { background-color: #ea4335; }
        
        .optimize-btn {
            background: linear-gradient(135deg, #4285f4, #34a853);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .optimize-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(66, 133, 244, 0.4);
        }
        
        #performance-chart { 
            width: 100%; 
            height: 400px; 
            background: rgba(255, 255, 255, 0.5);
            border-radius: 12px;
        }
        
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .connected {
            background-color: rgba(52, 168, 83, 0.1);
            color: #34a853;
            border: 1px solid #34a853;
        }
        
        .disconnected {
            background-color: rgba(234, 67, 53, 0.1);
            color: #ea4335;
            border: 1px solid #ea4335;
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connection-status">Connecting...</div>
    
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <p>Intelligent storage format optimization for distributed log processing</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📊 Storage Statistics</h3>
                <div id="storage-stats">
                    <div class="metric">
                        <span>Total Storage</span>
                        <span class="metric-value" id="total-storage">Loading...</span>
                    </div>
                    <div class="metric">
                        <span>Compression Savings</span>
                        <span class="metric-value" id="compression-savings">Loading...</span>
                    </div>
                    <div class="metric">
                        <span>Active Partitions</span>
                        <span class="metric-value" id="active-partitions">Loading...</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🎯 Format Distribution</h3>
                <div id="format-distribution">
                    <div class="metric">
                        <span><span class="status-indicator status-green"></span>Row-Oriented</span>
                        <span class="metric-value" id="row-count">0</span>
                    </div>
                    <div class="metric">
                        <span><span class="status-indicator status-yellow"></span>Columnar</span>
                        <span class="metric-value" id="columnar-count">0</span>
                    </div>
                    <div class="metric">
                        <span><span class="status-indicator status-red"></span>Hybrid</span>
                        <span class="metric-value" id="hybrid-count">0</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>⚡ Performance Metrics</h3>
                <div id="performance-metrics">
                    <div class="metric">
                        <span>Avg Query Time</span>
                        <span class="metric-value" id="avg-query-time">Loading...</span>
                    </div>
                    <div class="metric">
                        <span>Optimization Score</span>
                        <span class="metric-value" id="optimization-score">Loading...</span>
                    </div>
                </div>
                <button class="optimize-btn" onclick="triggerOptimization()">
                    🚀 Optimize All
                </button>
            </div>
        </div>
        
        <div class="card">
            <h3>📈 Performance Trends</h3>
            <div id="performance-chart"></div>
        </div>
    </div>

    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        let socket;
        let isConnected = false;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            socket = new WebSocket(wsUrl);
            
            socket.onopen = function(event) {
                isConnected = true;
                updateConnectionStatus();
                console.log('WebSocket connected');
            };
            
            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'stats_update') {
                    updateDashboard(data.data);
                }
            };
            
            socket.onclose = function(event) {
                isConnected = false;
                updateConnectionStatus();
                console.log('WebSocket disconnected');
                // Reconnect after 3 seconds
                setTimeout(connectWebSocket, 3000);
            };
            
            socket.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        function updateConnectionStatus() {
            const status = document.getElementById('connection-status');
            if (isConnected) {
                status.textContent = '🟢 Connected';
                status.className = 'connection-status connected';
            } else {
                status.textContent = '🔴 Disconnected';
                status.className = 'connection-status disconnected';
            }
        }
        
        function updateDashboard(stats) {
            // Update storage statistics
            document.getElementById('total-storage').textContent = `${stats.total_storage_mb} MB`;
            document.getElementById('compression-savings').textContent = `${stats.compression_savings}%`;
            document.getElementById('active-partitions').textContent = Object.keys(stats.partitions).length;
            
            // Update format distribution
            const formatDist = stats.format_distribution || {};
            document.getElementById('row-count').textContent = formatDist.row || 0;
            document.getElementById('columnar-count').textContent = formatDist.columnar || 0;
            document.getElementById('hybrid-count').textContent = formatDist.hybrid || 0;
            
            // Calculate average query time across all partitions
            const partitions = Object.values(stats.partitions);
            const avgQueryTime = partitions.length > 0 
                ? partitions.reduce((sum, p) => sum + p.avg_query_time, 0) / partitions.length
                : 0;
            document.getElementById('avg-query-time').textContent = `${avgQueryTime.toFixed(3)}s`;
            
            // Calculate optimization score (placeholder)
            const optimizationScore = Math.min(100, Math.max(0, 100 - (avgQueryTime * 1000)));
            document.getElementById('optimization-score').textContent = `${optimizationScore.toFixed(0)}/100`;
        }
        
        async function triggerOptimization() {
            try {
                const response = await fetch('/api/optimize/default', { method: 'POST' });
                const result = await response.json();
                console.log('Optimization triggered:', result);
                // Show notification or update UI
            } catch (error) {
                console.error('Optimization failed:', error);
            }
        }
        
        // Initialize dashboard
        connectWebSocket();
        
        // Load initial performance chart
        fetch('/api/performance-chart/default')
            .then(response => response.json())
            .then(chartData => {
                if (!chartData.error) {
                    Plotly.newPlot('performance-chart', chartData.data, chartData.layout, {
                        responsive: true,
                        displayModeBar: false
                    });
                }
            })
            .catch(error => console.error('Chart loading failed:', error));
    </script>
</body>
</html>
'''
EOF

# Create template directory and dashboard template
mkdir -p src/web/templates
cat > src/web/templates/dashboard.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Google Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .header h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }
        
        .card h3 {
            color: #4285f4;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        
        .metric:last-child { border-bottom: none; }
        
        .metric-value {
            font-weight: 600;
            color: #34a853;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-green { background-color: #34a853; }
        .status-yellow { background-color: #fbbc05; }
        .status-red { background-color: #ea4335; }
        
        .optimize-btn {
            background: linear-gradient(135deg, #4285f4, #34a853);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .optimize-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(66, 133, 244, 0.4);
        }
        
        #performance-chart { 
            width: 100%; 
            height: 400px; 
            background: rgba(255, 255, 255, 0.5);
            border-radius: 12px;
        }
        
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .connected {
            background-color: rgba(52, 168, 83, 0.1);
            color: #34a853;
            border: 1px solid #34a853;
        }
        
        .disconnected {
            background-color: rgba(234, 67, 53, 0.1);
            color: #ea4335;
            border: 1px solid #ea4335;
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connection-status">Connecting...</div>
    
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <p>Intelligent storage format optimization for distributed log processing</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📊 Storage Statistics</h3>
                <div id="storage-stats">
                    <div class="metric">
                        <span>Total Storage</span>
                        <span class="metric-value" id="total-storage">Loading...</span>
                    </div>
                    <div class="metric">
                        <span>Compression Savings</span>
                        <span class="metric-value" id="compression-savings">Loading...</span>
                    </div>
                    <div class="metric">
                        <span>Active Partitions</span>
                        <span class="metric-value" id="active-partitions">Loading...</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🎯 Format Distribution</h3>
                <div id="format-distribution">
                    <div class="metric">
                        <span><span class="status-indicator status-green"></span>Row-Oriented</span>
                        <span class="metric-value" id="row-count">0</span>
                    </div>
                    <div class="metric">
                        <span><span class="status-indicator status-yellow"></span>Columnar</span>
                        <span class="metric-value" id="columnar-count">0</span>
                    </div>
                    <div class="metric">
                        <span><span class="status-indicator status-red"></span>Hybrid</span>
                        <span class="metric-value" id="hybrid-count">0</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>⚡ Performance Metrics</h3>
                <div id="performance-metrics">
                    <div class="metric">
                        <span>Avg Query Time</span>
                        <span class="metric-value" id="avg-query-time">Loading...</span>
                    </div>
                    <div class="metric">
                        <span>Optimization Score</span>
                        <span class="metric-value" id="optimization-score">Loading...</span>
                    </div>
                </div>
                <button class="optimize-btn" onclick="triggerOptimization()">
                    🚀 Optimize All
                </button>
            </div>
        </div>
        
        <div class="card">
            <h3>📈 Performance Trends</h3>
            <div id="performance-chart"></div>
        </div>
    </div>

    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        let socket;
        let isConnected = false;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            socket = new WebSocket(wsUrl);
            
            socket.onopen = function(event) {
                isConnected = true;
                updateConnectionStatus();
                console.log('WebSocket connected');
            };
            
            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'stats_update') {
                    updateDashboard(data.data);
                }
            };
            
            socket.onclose = function(event) {
                isConnected = false;
                updateConnectionStatus();
                console.log('WebSocket disconnected');
                // Reconnect after 3 seconds
                setTimeout(connectWebSocket, 3000);
            };
            
            socket.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        function updateConnectionStatus() {
            const status = document.getElementById('connection-status');
            if (isConnected) {
                status.textContent = '🟢 Connected';
                status.className = 'connection-status connected';
            } else {
                status.textContent = '🔴 Disconnected';
                status.className = 'connection-status disconnected';
            }
        }
        
        function updateDashboard(stats) {
            // Update storage statistics
            document.getElementById('total-storage').textContent = `${stats.total_storage_mb} MB`;
            document.getElementById('compression-savings').textContent = `${stats.compression_savings}%`;
            document.getElementById('active-partitions').textContent = Object.keys(stats.partitions).length;
            
            // Update format distribution
            const formatDist = stats.format_distribution || {};
            document.getElementById('row-count').textContent = formatDist.row || 0;
            document.getElementById('columnar-count').textContent = formatDist.columnar || 0;
            document.getElementById('hybrid-count').textContent = formatDist.hybrid || 0;
            
            // Calculate average query time across all partitions
            const partitions = Object.values(stats.partitions);
            const avgQueryTime = partitions.length > 0 
                ? partitions.reduce((sum, p) => sum + p.avg_query_time, 0) / partitions.length
                : 0;
            document.getElementById('avg-query-time').textContent = `${avgQueryTime.toFixed(3)}s`;
            
            // Calculate optimization score (placeholder)
            const optimizationScore = Math.min(100, Math.max(0, 100 - (avgQueryTime * 1000)));
            document.getElementById('optimization-score').textContent = `${optimizationScore.toFixed(0)}/100`;
        }
        
        async function triggerOptimization() {
            try {
                const response = await fetch('/api/optimize/default', { method: 'POST' });
                const result = await response.json();
                console.log('Optimization triggered:', result);
                // Show notification or update UI
            } catch (error) {
                console.error('Optimization failed:', error);
            }
        }
        
        // Initialize dashboard
        connectWebSocket();
        
        // Load initial performance chart
        fetch('/api/performance-chart/default')
            .then(response => response.json())
            .then(chartData => {
                if (!chartData.error) {
                    Plotly.newPlot('performance-chart', chartData.data, chartData.layout, {
                        responsive: true,
                        displayModeBar: false
                    });
                }
            })
            .catch(error => console.error('Chart loading failed:', error));
    </script>
</body>
</html>
EOF

print_status "Web dashboard created"

# Create main application
cat > src/main.py << 'EOF'
"""
Storage Format Optimization System - Main Application
"""
import asyncio
import uvicorn
from storage.storage_engine import AdaptiveStorageEngine
from analyzer.pattern_analyzer import AccessPatternAnalyzer
from web.dashboard import StorageOptimizationDashboard
from datetime import datetime
import json
import random

class StorageOptimizationSystem:
    def __init__(self):
        self.storage_engine = AdaptiveStorageEngine("data")
        self.pattern_analyzer = AccessPatternAnalyzer()
        self.dashboard = StorageOptimizationDashboard(self.storage_engine, self.pattern_analyzer)
        
    async def start(self):
        """Start the optimization system"""
        print("🚀 Starting Storage Format Optimization System")
        print("=" * 50)
        
        # Generate sample data for demonstration
        await self.generate_demo_data()
        
        # Start the web dashboard
        print("🌐 Starting web dashboard...")
        config = uvicorn.Config(
            app=self.dashboard.app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        print("✅ Storage Optimization System ready!")
        print("📊 Dashboard: http://localhost:8000")
        print("🔄 System will continuously optimize storage formats...")
        
        await server.serve()
    
    async def generate_demo_data(self):
        """Generate demonstration data with different query patterns"""
        print("📝 Generating demonstration data...")
        
        # Sample log entries with realistic structure
        sample_logs = []
        services = ['web-api', 'user-service', 'payment-service', 'analytics']
        log_levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
        
        for i in range(100):
            log_entry = {
                'id': f"log_{i:04d}",
                'timestamp': datetime.now().isoformat(),
                'service': random.choice(services),
                'level': random.choice(log_levels),
                'message': f"Sample log message {i}",
                'user_id': f"user_{random.randint(1, 1000):04d}",
                'request_id': f"req_{random.randint(1, 10000):06d}",
                'duration_ms': random.randint(10, 2000),
                'status_code': random.choice([200, 201, 400, 404, 500]),
                'ip_address': f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                'metadata': {
                    'region': random.choice(['us-west-1', 'us-east-1', 'eu-west-1']),
                    'version': f"v{random.randint(1, 5)}.{random.randint(0, 10)}",
                    'environment': random.choice(['prod', 'staging', 'dev'])
                }
            }
            sample_logs.append(log_entry)
        
        # Write logs to different partitions
        partitions = ['web-logs', 'api-logs', 'error-logs']
        for partition in partitions:
            partition_logs = sample_logs[:30]  # Use subset for each partition
            await self.storage_engine.write_logs(partition_logs, partition)
        
        # Simulate different query patterns
        await self.simulate_query_patterns()
        
        print(f"✅ Generated {len(sample_logs)} demo logs across {len(partitions)} partitions")
    
    async def simulate_query_patterns(self):
        """Simulate different query patterns to trigger format optimization"""
        print("🔍 Simulating query patterns...")
        
        # Pattern 1: Full record queries (row-oriented friendly)
        for i in range(10):
            query = {'level': 'ERROR'}
            results = await self.storage_engine.read_logs(query, 'error-logs')
            self.pattern_analyzer.record_query(
                'error-logs', query, 0.05, len(results)
            )
        
        # Pattern 2: Analytical queries (columnar friendly)
        for i in range(20):
            query = {
                'columns': ['timestamp', 'duration_ms', 'status_code'],
                'aggregation': True
            }
            results = await self.storage_engine.read_logs(query, 'api-logs')
            self.pattern_analyzer.record_query(
                'api-logs', query, 0.15, len(results)
            )
        
        # Pattern 3: Mixed queries (hybrid friendly)
        for i in range(15):
            query = {
                'service': 'web-api',
                'columns': ['timestamp', 'message', 'user_id', 'status_code']
            }
            results = await self.storage_engine.read_logs(query, 'web-logs')
            self.pattern_analyzer.record_query(
                'web-logs', query, 0.08, len(results)
            )
        
        print("✅ Query pattern simulation completed")

async def main():
    system = StorageOptimizationSystem()
    await system.start()

if __name__ == "__main__":
    asyncio.run(main())
EOF

print_status "Main application created"

# Create comprehensive test suite
cat > tests/test_storage_optimization.py << 'EOF'
"""
Comprehensive test suite for storage format optimization
"""
import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, 'src')

from storage.storage_engine import AdaptiveStorageEngine, StorageFormat
from analyzer.pattern_analyzer import AccessPatternAnalyzer

class TestStorageEngine:
    @pytest.fixture
    def temp_dir(self):
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def storage_engine(self, temp_dir):
        return AdaptiveStorageEngine(temp_dir)
    
    @pytest.fixture
    def sample_logs(self):
        return [
            {
                'id': 'log_001',
                'timestamp': datetime.now().isoformat(),
                'service': 'web-api',
                'level': 'INFO',
                'message': 'User logged in',
                'user_id': 'user_123',
                'duration_ms': 45
            },
            {
                'id': 'log_002',
                'timestamp': datetime.now().isoformat(),
                'service': 'payment',
                'level': 'ERROR',
                'message': 'Payment failed',
                'user_id': 'user_456',
                'duration_ms': 1200
            }
        ]
    
    @pytest.mark.asyncio
    async def test_write_logs(self, storage_engine, sample_logs):
        """Test writing logs to storage"""
        result = await storage_engine.write_logs(sample_logs, "test_partition")
        assert result is True
        
        # Verify logs were written
        stats = storage_engine.get_optimization_stats()
        assert 'test_partition' in stats['partitions']
        assert stats['partitions']['test_partition']['writes'] == 2
    
    @pytest.mark.asyncio
    async def test_read_logs(self, storage_engine, sample_logs):
        """Test reading logs from storage"""
        # First write some logs
        await storage_engine.write_logs(sample_logs, "test_partition")
        
        # Then read them back
        query = {'level': 'INFO'}
        results = await storage_engine.read_logs(query, "test_partition")
        
        assert len(results) == 1
        assert results[0]['level'] == 'INFO'
        assert results[0]['service'] == 'web-api'
    
    @pytest.mark.asyncio
    async def test_query_filtering(self, storage_engine, sample_logs):
        """Test query filtering functionality"""
        await storage_engine.write_logs(sample_logs, "test_partition")
        
        # Test service filter
        query = {'service': 'payment'}
        results = await storage_engine.read_logs(query, "test_partition")
        assert len(results) == 1
        assert results[0]['service'] == 'payment'
        
        # Test level filter
        query = {'level': 'ERROR'}
        results = await storage_engine.read_logs(query, "test_partition")
        assert len(results) == 1
        assert results[0]['level'] == 'ERROR'
    
    def test_optimization_stats(self, storage_engine):
        """Test optimization statistics"""
        stats = storage_engine.get_optimization_stats()
        
        assert 'partitions' in stats
        assert 'total_storage_mb' in stats
        assert 'compression_savings' in stats
        assert 'format_distribution' in stats

class TestPatternAnalyzer:
    @pytest.fixture
    def pattern_analyzer(self):
        return AccessPatternAnalyzer()
    
    def test_record_query(self, pattern_analyzer):
        """Test query recording functionality"""
        query = {'level': 'ERROR', 'service': 'web-api'}
        pattern_analyzer.record_query("test_partition", query, 0.1, 5)
        
        recommendations = pattern_analyzer.get_recommendations("test_partition")
        assert 'recommended_format' in recommendations
        assert 'confidence' in recommendations
    
    def test_analytical_query_classification(self, pattern_analyzer):
        """Test analytical query pattern detection"""
        # Record multiple analytical queries
        for _ in range(10):
            query = {
                'columns': ['timestamp', 'duration_ms'],
                'aggregation': True
            }
            pattern_analyzer.record_query("analytics_partition", query, 0.2, 1000)
        
        recommendations = pattern_analyzer.get_recommendations("analytics_partition")
        assert recommendations['recommended_format'] == 'columnar'
        assert recommendations['analytical_ratio'] > 0.5
    
    def test_full_record_query_classification(self, pattern_analyzer):
        """Test full record query pattern detection"""
        # Record multiple full record queries
        for _ in range(10):
            query = {'level': 'INFO'}  # Full record query (no column specification)
            pattern_analyzer.record_query("logs_partition", query, 0.1, 10)
        
        recommendations = pattern_analyzer.get_recommendations("logs_partition")
        assert recommendations['recommended_format'] == 'row_oriented'
        assert recommendations['full_record_ratio'] > 0.5
    
    def test_mixed_query_pattern(self, pattern_analyzer):
        """Test mixed query pattern detection"""
        # Record mixed query patterns
        for i in range(10):
            if i % 2 == 0:
                query = {'columns': ['timestamp', 'level']}  # Analytical
            else:
                query = {'service': 'web-api'}  # Full record
            
            pattern_analyzer.record_query("mixed_partition", query, 0.15, 20)
        
        recommendations = pattern_analyzer.get_recommendations("mixed_partition")
        assert recommendations['recommended_format'] == 'hybrid'
    
    def test_optimization_insights(self, pattern_analyzer):
        """Test optimization insights generation"""
        # Record some queries
        query = {'level': 'ERROR'}
        pattern_analyzer.record_query("test_partition", query, 0.1, 5)
        
        insights = pattern_analyzer.get_optimization_insights()
        
        assert 'partitions_analyzed' in insights
        assert 'total_queries' in insights
        assert 'recommendations' in insights
        assert insights['partitions_analyzed'] >= 1
        assert insights['total_queries'] >= 1

class TestStorageFormats:
    @pytest.fixture
    def temp_dir(self):
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.mark.asyncio
    async def test_row_storage(self, temp_dir):
        """Test row-oriented storage"""
        from storage.storage_engine import RowStorage
        
        storage = RowStorage(Path(temp_dir))
        logs = [
            {'id': '1', 'message': 'test1'},
            {'id': '2', 'message': 'test2'}
        ]
        
        # Test write
        result = await storage.write(logs, "test")
        assert result is True
        
        # Test read
        results = await storage.read({}, "test")
        assert len(results) == 2
        assert results[0]['id'] == '1'
    
    @pytest.mark.asyncio
    async def test_columnar_storage(self, temp_dir):
        """Test columnar storage"""
        from storage.storage_engine import ColumnarStorage
        
        storage = ColumnarStorage(Path(temp_dir))
        logs = [
            {'id': 1, 'message': 'test1', 'level': 'INFO'},
            {'id': 2, 'message': 'test2', 'level': 'ERROR'}
        ]
        
        # Test write
        result = await storage.write(logs, "test")
        assert result is True
        
        # Test read with column pruning
        results = await storage.read({'columns': ['id', 'level']}, "test")
        assert len(results) == 2
        assert 'id' in results[0]
        assert 'level' in results[0]
    
    @pytest.mark.asyncio
    async def test_hybrid_storage(self, temp_dir):
        """Test hybrid storage"""
        from storage.storage_engine import HybridStorage
        
        storage = HybridStorage(Path(temp_dir))
        logs = [
            {'id': '1', 'message': 'test1'},
            {'id': '2', 'message': 'test2'}
        ]
        
        # Test write (should go to hot storage)
        result = await storage.write(logs, "test")
        assert result is True
        
        # Test read (should read from hot storage)
        results = await storage.read({}, "test")
        assert len(results) == 2

# Performance benchmarks
class TestPerformance:
    @pytest.mark.asyncio
    async def test_write_performance(self):
        """Test write performance across formats"""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_engine = AdaptiveStorageEngine(temp_dir)
            
            # Generate test data
            logs = []
            for i in range(1000):
                logs.append({
                    'id': f'log_{i}',
                    'timestamp': datetime.now().isoformat(),
                    'message': f'Test message {i}',
                    'level': 'INFO',
                    'service': 'test-service'
                })
            
            # Measure write time
            start_time = time.time()
            result = await storage_engine.write_logs(logs, "performance_test")
            write_time = time.time() - start_time
            
            assert result is True
            assert write_time < 2.0  # Should complete within 2 seconds
            print(f"✅ Write performance: {len(logs)} logs in {write_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_read_performance(self):
        """Test read performance"""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_engine = AdaptiveStorageEngine(temp_dir)
            
            # Write test data
            logs = [
                {
                    'id': f'log_{i}',
                    'level': 'INFO' if i % 2 == 0 else 'ERROR',
                    'service': f'service_{i % 3}',
                    'message': f'Message {i}'
                }
                for i in range(100)
            ]
            await storage_engine.write_logs(logs, "perf_test")
            
            # Measure read time
            start_time = time.time()
            results = await storage_engine.read_logs({'level': 'INFO'}, "perf_test")
            read_time = time.time() - start_time
            
            assert len(results) == 50  # Half should be INFO level
            assert read_time < 1.0  # Should complete within 1 second
            print(f"✅ Read performance: {len(results)} results in {read_time:.3f}s")

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
EOF

print_status "Test suite created"

# Create configuration file
cat > config/config.py << 'EOF'
"""
Configuration settings for storage optimization system
"""
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class StorageConfig:
    # Storage paths
    base_data_path: str = "data"
    backup_path: str = "backups"
    
    # Format selection parameters
    analytical_threshold: float = 0.6
    full_record_threshold: float = 0.7
    
    # Compression settings
    enable_compression: bool = True
    compression_algorithm: str = "lz4"  # lz4, snappy, gzip
    
    # Performance settings
    batch_size: int = 1000
    max_memory_mb: int = 512
    
    # Query pattern analysis
    pattern_history_hours: int = 24
    min_queries_for_decision: int = 10
    
    # Migration settings
    auto_migration_enabled: bool = True
    migration_batch_size: int = 5000

@dataclass
class DashboardConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    auto_reload: bool = True
    log_level: str = "info"
    
    # WebSocket settings
    websocket_heartbeat: int = 5
    max_connections: int = 100

# Default configuration
DEFAULT_CONFIG = {
    'storage': StorageConfig(),
    'dashboard': DashboardConfig()
}

def load_config() -> Dict[str, Any]:
    """Load configuration from file or return defaults"""
    return DEFAULT_CONFIG
EOF

print_status "Configuration created"

# Create Docker setup
cat > docker/Dockerfile << 'EOF'
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
COPY config/ ./config/
COPY tests/ ./tests/

# Create data directories
RUN mkdir -p data logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "src/main.py"]
EOF

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  storage-optimizer:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONPATH=/app/src
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/stats"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  storage_data:
  logs:
EOF

print_status "Docker setup created"

# Create demo script
cat > demo.py << 'EOF'
"""
Storage Format Optimization Demo
"""
import asyncio
import json
from datetime import datetime
import random
import time

# Add src to Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storage.storage_engine import AdaptiveStorageEngine
from analyzer.pattern_analyzer import AccessPatternAnalyzer

class StorageDemo:
    def __init__(self):
        self.storage_engine = AdaptiveStorageEngine("demo_data")
        self.pattern_analyzer = AccessPatternAnalyzer()
    
    async def run_demo(self):
        """Run comprehensive storage optimization demonstration"""
        print("🚀 Storage Format Optimization Demo")
        print("=" * 50)
        
        # Phase 1: Generate sample data
        await self.phase1_generate_data()
        
        # Phase 2: Demonstrate different query patterns
        await self.phase2_query_patterns()
        
        # Phase 3: Show optimization recommendations
        await self.phase3_optimization()
        
        # Phase 4: Performance comparison
        await self.phase4_performance()
        
        print("\n✅ Demo completed successfully!")
        print("🌐 Start the web dashboard with: python src/main.py")
    
    async def phase1_generate_data(self):
        """Generate realistic log data for demonstration"""
        print("\n📝 Phase 1: Generating Sample Data")
        print("-" * 30)
        
        # Create different types of log entries
        web_logs = []
        api_logs = []
        error_logs = []
        
        for i in range(200):
            timestamp = datetime.now().isoformat()
            
            # Web server logs
            web_log = {
                'id': f'web_{i:04d}',
                'timestamp': timestamp,
                'service': 'web-server',
                'level': random.choice(['INFO', 'DEBUG']),
                'method': random.choice(['GET', 'POST', 'PUT']),
                'path': random.choice(['/api/users', '/api/orders', '/health']),
                'status_code': random.choice([200, 201, 304, 404]),
                'response_time': random.randint(10, 500),
                'ip_address': f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
                'user_agent': 'Mozilla/5.0...'
            }
            web_logs.append(web_log)
            
            # API logs
            if i % 3 == 0:
                api_log = {
                    'id': f'api_{i:04d}',
                    'timestamp': timestamp,
                    'service': 'payment-api',
                    'level': 'INFO',
                    'transaction_id': f'txn_{random.randint(1000, 9999)}',
                    'amount': random.randint(10, 1000),
                    'currency': 'USD',
                    'status': random.choice(['success', 'pending', 'failed']),
                    'processing_time': random.randint(50, 2000)
                }
                api_logs.append(api_log)
            
            # Error logs
            if i % 10 == 0:
                error_log = {
                    'id': f'error_{i:04d}',
                    'timestamp': timestamp,
                    'service': random.choice(['web-server', 'payment-api', 'user-service']),
                    'level': 'ERROR',
                    'error_code': random.choice(['E001', 'E002', 'E003']),
                    'error_message': 'Sample error message',
                    'stack_trace': 'Stack trace details...',
                    'affected_user': f'user_{random.randint(1, 100)}'
                }
                error_logs.append(error_log)
        
        # Store in different partitions
        await self.storage_engine.write_logs(web_logs, 'web-logs')
        await self.storage_engine.write_logs(api_logs, 'api-logs')
        await self.storage_engine.write_logs(error_logs, 'error-logs')
        
        print(f"✅ Generated {len(web_logs)} web logs")
        print(f"✅ Generated {len(api_logs)} API logs")
        print(f"✅ Generated {len(error_logs)} error logs")
    
    async def phase2_query_patterns(self):
        """Demonstrate different query patterns"""
        print("\n🔍 Phase 2: Demonstrating Query Patterns")
        print("-" * 40)
        
        # Pattern 1: Full record queries (row-oriented friendly)
        print("📋 Pattern 1: Full record access (row-oriented optimal)")
        start_time = time.time()
        
        for i in range(5):
            query = {'level': 'ERROR'}
            results = await self.storage_engine.read_logs(query, 'error-logs')
            self.pattern_analyzer.record_query('error-logs', query, 0.1, len(results))
        
        full_time = time.time() - start_time
        print(f"   ⏱️  5 full record queries: {full_time:.3f}s")
        
        # Pattern 2: Analytical queries (columnar friendly)
        print("📊 Pattern 2: Analytical access (columnar optimal)")
        start_time = time.time()
        
        for i in range(10):
            query = {
                'columns': ['timestamp', 'response_time', 'status_code'],
                'aggregation': True,
                'service': 'web-server'
            }
            results = await self.storage_engine.read_logs(query, 'web-logs')
            self.pattern_analyzer.record_query('web-logs', query, 0.2, len(results))
        
        analytical_time = time.time() - start_time
        print(f"   ⏱️  10 analytical queries: {analytical_time:.3f}s")
        
        # Pattern 3: Mixed queries (hybrid friendly)
        print("🔀 Pattern 3: Mixed access (hybrid optimal)")
        start_time = time.time()
        
        for i in range(8):
            if i % 2 == 0:
                query = {'transaction_id': f'txn_{random.randint(1000, 9999)}'}
            else:
                query = {'columns': ['amount', 'currency', 'status']}
            
            results = await self.storage_engine.read_logs(query, 'api-logs')
            self.pattern_analyzer.record_query('api-logs', query, 0.15, len(results))
        
        mixed_time = time.time() - start_time
        print(f"   ⏱️  8 mixed queries: {mixed_time:.3f}s")
    
    async def phase3_optimization(self):
        """Show optimization recommendations"""
        print("\n🎯 Phase 3: Storage Format Recommendations")
        print("-" * 45)
        
        partitions = ['error-logs', 'web-logs', 'api-logs']
        
        for partition in partitions:
            recommendations = self.pattern_analyzer.get_recommendations(partition)
            
            print(f"\n📊 Partition: {partition}")
            print(f"   Recommended Format: {recommendations['recommended_format'].upper()}")
            print(f"   Confidence: {recommendations['confidence'].upper()}")
            print(f"   Analytical Ratio: {recommendations['analytical_ratio']:.2f}")
            print(f"   Full Record Ratio: {recommendations['full_record_ratio']:.2f}")
            print(f"   Total Queries: {recommendations['total_queries']}")
    
    async def phase4_performance(self):
        """Show performance comparison"""
        print("\n⚡ Phase 4: Performance Analysis")
        print("-" * 35)
        
        # Get current system stats
        stats = self.storage_engine.get_optimization_stats()
        insights = self.pattern_analyzer.get_optimization_insights()
        
        print(f"📈 System Statistics:")
        print(f"   Total Storage: {stats['total_storage_mb']:.2f} MB")
        print(f"   Active Partitions: {len(stats['partitions'])}")
        print(f"   Queries Analyzed: {insights['total_queries']}")
        
        print(f"\n🔍 Per-Partition Performance:")
        for partition, metrics in stats['partitions'].items():
            print(f"   {partition}:")
            print(f"     - Reads: {metrics['reads']}")
            print(f"     - Writes: {metrics['writes']}")
            print(f"     - Avg Query Time: {metrics['avg_query_time']:.3f}s")
            print(f"     - Storage: {metrics['storage_mb']:.2f} MB")

async def main():
    demo = StorageDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())
EOF

print_status "Demo script created"

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt

print_status "Dependencies installed"

# Set Python path for imports
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
print_status "Python path configured"

# Run tests
print_info "Running unit tests..."
python -m pytest tests/test_storage_optimization.py -v

if [ $? -eq 0 ]; then
    print_status "All tests passed"
else
    print_warning "Some tests failed, but continuing with demo..."
fi

# Run demonstration
print_info "Running system demonstration..."
python demo.py

print_status "Demonstration completed"

# Build and test with Docker (optional)
if command -v docker &> /dev/null; then
    print_info "Building Docker image..."
    docker build -t storage-optimizer -f docker/Dockerfile .
    
    if [ $? -eq 0 ]; then
        print_status "Docker image built successfully"
        
        print_info "Testing Docker deployment..."
        docker-compose up -d
        
        # Wait for service to be ready
        sleep 10
        
        # Test the API
        if curl -f http://localhost:8000/api/stats &> /dev/null; then
            print_status "Docker deployment successful"
            print_info "Dashboard available at: http://localhost:8000"
        else
            print_warning "Docker deployment might need more time to start"
        fi
        
        # Clean up
        docker-compose down
    else
        print_warning "Docker build failed, but system works without Docker"
    fi
else
    print_info "Docker not available, skipping containerization"
fi

# Final instructions
echo
echo "🎉 Storage Format Optimization System Setup Complete!"
echo "=" * 55
echo
echo "📁 Project Structure:"
echo "   ├── src/               # Source code"
echo "   │   ├── storage/       # Storage engine"
echo "   │   ├── analyzer/      # Pattern analyzer"
echo "   │   └── web/           # Dashboard"
echo "   ├── tests/             # Test suite"
echo "   ├── config/            # Configuration"
echo "   ├── data/              # Storage data"
echo "   └── docker/            # Containerization"
echo
echo "🚀 Quick Start Commands:"
echo "   python src/main.py                    # Start the system"
echo "   python demo.py                       # Run demonstration"
echo "   python -m pytest tests/ -v           # Run tests"
echo "   docker-compose up                    # Docker deployment"
echo
echo "🌐 Web Dashboard: http://localhost:8000"
echo "📊 API Endpoints:"
echo "   GET  /api/stats                      # System statistics"
echo "   GET  /api/recommendations/<partition> # Format recommendations"
echo "   POST /api/optimize/<partition>        # Trigger optimization"
echo
echo "✅ System Features:"
echo "   • Adaptive storage format selection"
echo "   • Real-time query pattern analysis"
echo "   • Multi-format storage engine (row/columnar/hybrid)"
echo "   • Performance monitoring dashboard"
echo "   • Automatic format optimization"
echo
print_status "Setup completed successfully! 🎯"