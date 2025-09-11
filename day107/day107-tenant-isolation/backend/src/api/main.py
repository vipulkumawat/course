"""Main FastAPI application."""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional
from core.quota_engine import QuotaEngine
from services.tenant_service import TenantService
from middleware.isolation import TenantIsolationMiddleware, get_tenant_context, verify_tenant_access

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
quota_engine = QuotaEngine()
tenant_service = TenantService(quota_engine)
isolation_middleware = TenantIsolationMiddleware(quota_engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    logger.info("Starting tenant isolation system...")
    await quota_engine.start_monitoring()
    yield
    # Shutdown
    logger.info("Shutting down tenant isolation system...")
    await quota_engine.stop_monitoring()

app = FastAPI(
    title="Tenant Isolation & Resource Quotas",
    description="Day 107: Multi-tenant system with resource isolation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class LogRequest(BaseModel):
    message: str
    level: str = "INFO"
    metadata: Optional[Dict] = None

class QuotaUpdateRequest(BaseModel):
    cpu_cores: Optional[float] = None
    memory_mb: Optional[int] = None
    storage_mb: Optional[int] = None
    requests_per_minute: Optional[int] = None
    concurrent_connections: Optional[int] = None

@app.middleware("http")
async def tenant_isolation_middleware(request: Request, call_next):
    """Apply tenant isolation to all requests."""
    return await isolation_middleware(request, call_next)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Tenant Isolation & Resource Quotas System", "day": 107}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2025-06-16T10:00:00Z"}

@app.get("/api/tenants")
async def get_tenants():
    """Get all tenants."""
    tenants = tenant_service.get_all_tenants()
    return {"tenants": tenants}

@app.get("/api/tenants/{tenant_id}")
async def get_tenant(tenant_id: str):
    """Get specific tenant."""
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@app.get("/api/tenants/{tenant_id}/metrics")
async def get_tenant_metrics(tenant_id: str):
    """Get real-time metrics for tenant."""
    metrics = tenant_service.get_tenant_metrics(tenant_id)
    return metrics

@app.post("/api/tenants/{tenant_id}/logs")
async def process_log(tenant_id: str, log_request: LogRequest, request: Request):
    """Process a log entry for tenant."""
    try:
        result = await tenant_service.process_tenant_log(tenant_id, {
            "message": log_request.message,
            "level": log_request.level,
            "metadata": log_request.metadata or {}
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quota-status")
async def get_quota_status():
    """Get quota status for all tenants."""
    status = {}
    for tenant_id in quota_engine.quotas.keys():
        status[tenant_id] = {
            "utilization": quota_engine.get_quota_utilization(tenant_id),
            "metrics": tenant_service.get_tenant_metrics(tenant_id)
        }
    return status

@app.post("/api/simulate-load/{tenant_id}")
async def simulate_load(tenant_id: str):
    """Simulate load for testing quota enforcement."""
    try:
        tasks = []
        for i in range(10):  # Simulate 10 concurrent requests
            task = tenant_service.process_tenant_log(tenant_id, {
                "message": f"Simulated log entry {i}",
                "level": "INFO",
                "simulation": True
            })
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum(1 for r in results if not isinstance(r, Exception))
        
        return {
            "message": f"Load simulation completed for {tenant_id}",
            "total_requests": len(tasks),
            "successful_requests": successful,
            "failed_requests": len(tasks) - successful
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket):
    """WebSocket endpoint for real-time metrics."""
    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        # Send initial connection confirmation
        await websocket.send_json({"type": "connected", "message": "WebSocket connected successfully"})
        
        while True:
            # Send current metrics for all tenants
            metrics = {}
            for tenant_id in quota_engine.quotas.keys():
                metrics[tenant_id] = tenant_service.get_tenant_metrics(tenant_id)
            
            await websocket.send_json({"type": "metrics", "data": metrics})
            await asyncio.sleep(2)  # Update every 2 seconds
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
