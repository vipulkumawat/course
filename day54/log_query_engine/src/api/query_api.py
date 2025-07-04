"""
FastAPI endpoints for SQL query processing
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
from datetime import datetime

from ..parser.sql_parser import SQLParser
from ..planner.query_planner import QueryPlanner, PartitionInfo
from ..executor.query_executor import QueryExecutor, NodeConnection

app = FastAPI(title="Distributed Log Query Engine", version="1.0.0")

# Initialize components
sql_parser = SQLParser()

# Mock partition metadata
partition_metadata = [
    PartitionInfo(
        node_id="node1",
        partition_id="partition_2025_01_15",
        time_range=(datetime(2025, 1, 15), datetime(2025, 1, 16)),
        indexed_fields={"timestamp", "level", "service"},
        record_count=100000,
        size_bytes=50000000
    ),
    PartitionInfo(
        node_id="node2",
        partition_id="partition_2025_01_16",
        time_range=(datetime(2025, 1, 16), datetime(2025, 1, 17)),
        indexed_fields={"timestamp", "level", "service"},
        record_count=150000,
        size_bytes=75000000
    ),
    PartitionInfo(
        node_id="node3",
        partition_id="partition_2025_01_17",
        time_range=(datetime(2025, 1, 17), datetime(2025, 1, 18)),
        indexed_fields={"timestamp", "level", "service"},
        record_count=120000,
        size_bytes=60000000
    )
]

query_planner = QueryPlanner(partition_metadata)

# Mock node connections
node_connections = [
    NodeConnection("node1", "localhost", 8001),
    NodeConnection("node2", "localhost", 8002),
    NodeConnection("node3", "localhost", 8003)
]

query_executor = QueryExecutor(node_connections)

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    timeout_seconds: Optional[int] = 30

class QueryResponse(BaseModel):
    query_id: str
    status: str
    results: List[Dict[str, Any]]
    execution_time_ms: float
    records_processed: int
    query_plan: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None

# Templates
templates = Jinja2Templates(directory="frontend/public")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve main query interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/query", response_model=QueryResponse)
async def execute_query(query_request: QueryRequest):
    """Execute SQL query against distributed log data"""
    try:
        # Parse query
        query_ast = sql_parser.parse(query_request.query)
        
        # Create execution plan
        query_plan = query_planner.create_execution_plan(query_ast)
        
        # Execute query
        execution_result = await query_executor.execute_query(
            query_plan, 
            query_request.timeout_seconds
        )
        
        return QueryResponse(
            query_id=execution_result.query_id,
            status=execution_result.status,
            results=execution_result.results,
            execution_time_ms=execution_result.execution_time_ms,
            records_processed=execution_result.records_processed,
            query_plan={
                "steps": len(query_plan.steps),
                "parallelism_level": query_plan.parallelism_level,
                "optimization_notes": query_plan.optimization_notes
            },
            errors=execution_result.errors
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/query/{query_id}/explain")
async def explain_query(query_id: str):
    """Get query execution plan explanation"""
    # For demonstration, return mock explanation
    return {
        "query_id": query_id,
        "execution_plan": {
            "steps": [
                {
                    "step_id": "filter_partition_2025_01_15",
                    "description": "Filter logs in partition 2025-01-15",
                    "estimated_cost": 100.0,
                    "parallelizable": True
                },
                {
                    "step_id": "global_aggregation",
                    "description": "Aggregate results from all partitions",
                    "estimated_cost": 50.0,
                    "parallelizable": False
                }
            ],
            "optimizations_applied": [
                "Partition pruning: 1/3 partitions selected",
                "Predicate pushdown: WHERE conditions pushed to storage layer"
            ]
        }
    }

@app.get("/api/partitions")
async def list_partitions():
    """List available data partitions"""
    return {
        "partitions": [
            {
                "partition_id": p.partition_id,
                "node_id": p.node_id,
                "time_range": {
                    "start": p.time_range[0].isoformat(),
                    "end": p.time_range[1].isoformat()
                },
                "record_count": p.record_count,
                "size_mb": p.size_bytes / 1024 / 1024,
                "indexed_fields": list(p.indexed_fields)
            }
            for p in partition_metadata
        ]
    }

@app.get("/api/health")
async def health_check():
    """Check system health"""
    node_health = await query_executor.health_check()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "parser": {"status": "healthy"},
            "planner": {"status": "healthy"},
            "executor": {"status": "healthy"}
        },
        "nodes": node_health
    }

@app.get("/api/examples")
async def get_query_examples():
    """Get example queries for testing"""
    return {
        "examples": [
            {
                "name": "Error Analysis",
                "query": "SELECT service, COUNT(*) as error_count FROM logs WHERE level = 'ERROR' AND timestamp > '2025-01-15' GROUP BY service ORDER BY error_count DESC LIMIT 10",
                "description": "Find services with the most errors"
            },
            {
                "name": "Performance Monitoring",
                "query": "SELECT service, AVG(response_time) as avg_response FROM logs WHERE timestamp > '2025-01-16' GROUP BY service ORDER BY avg_response DESC",
                "description": "Analyze average response times by service"
            },
            {
                "name": "Time Series Analysis",
                "query": "SELECT timestamp, COUNT(*) as log_count FROM logs WHERE level IN ('ERROR', 'WARNING') GROUP BY timestamp ORDER BY timestamp",
                "description": "Time series of error and warning logs"
            },
            {
                "name": "Message Search",
                "query": "SELECT * FROM logs WHERE message CONTAINS 'database timeout' AND timestamp > '2025-01-15' ORDER BY timestamp DESC LIMIT 50",
                "description": "Search for specific error messages"
            }
        ]
    }

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/public"), name="static")
