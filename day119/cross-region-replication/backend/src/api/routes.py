"""
API Routes for Cross-Region Replication System
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time

# Components will be injected via dependencies to avoid circular imports

api_router = APIRouter()

class LogData(BaseModel):
    message: str
    level: str = "info"
    service: str = "default"
    metadata: Optional[Dict[str, Any]] = {}

class ClientInfo(BaseModel):
    location: str = "us"
    client_id: str = "default"

@api_router.post("/logs/submit")
async def submit_log(log_data: LogData, location: str = "us", client_id: str = "default"):
    """Submit log data for cross-region replication"""
    try:
        # Get components from the app state
        from main import app
        replication_coordinator = app.state.replication_coordinator
        client_router = app.state.client_router
        
        # Create client info from query parameters
        client_info = ClientInfo(location=location, client_id=client_id)
            
        # Prepare data for routing
        data = {
            "message": log_data.message,
            "level": log_data.level, 
            "service": log_data.service,
            "metadata": log_data.metadata,
            "timestamp": time.time()
        }
        
        # Route request to appropriate region
        routing_result = await client_router.route_request(
            client_info.dict(), data
        )
        
        # Trigger replication to other regions
        source_region = routing_result["target_region"]
        await replication_coordinator.replicate_data(data, source_region)
        
        return {
            "status": "success",
            "routing_result": routing_result,
            "replication_triggered": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/regions")
async def get_regions():
    """Get all regions and their status"""
    from main import app
    region_manager = app.state.region_manager
    return region_manager.get_region_summary()

@api_router.get("/regions/{region_id}")
async def get_region(region_id: str):
    """Get specific region details"""
    from main import app
    region_manager = app.state.region_manager
    region = region_manager.get_region(region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
        
    return {
        "id": region.id,
        "name": region.name,
        "location": region.location,
        "status": region.status.value,
        "last_heartbeat": region.last_heartbeat,
        "latency_ms": int(region.connection_latency * 1000),
        "data_count": len(region.data_store)
    }

@api_router.get("/replication/metrics")
async def get_replication_metrics():
    """Get replication metrics"""
    from main import app
    replication_coordinator = app.state.replication_coordinator
    return replication_coordinator.get_metrics()

@api_router.get("/health/comprehensive") 
async def get_comprehensive_health():
    """Get comprehensive system health"""
    from main import app
    health_monitor = app.state.health_monitor
    return await health_monitor.get_comprehensive_status()

@api_router.get("/routing/stats")
async def get_routing_stats():
    """Get routing statistics"""
    from main import app
    client_router = app.state.client_router
    return client_router.get_routing_stats()

@api_router.post("/failover/{region_id}")
async def trigger_failover(region_id: str):
    """Manually trigger failover from a region"""
    try:
        from main import app
        replication_coordinator = app.state.replication_coordinator
        result = await replication_coordinator.trigger_failover(region_id)
        return {
            "status": "success" if result else "failed",
            "message": f"Failover triggered for region {region_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/recovery/{region_id}")
async def trigger_recovery(region_id: str):
    """Manually trigger recovery for a region"""
    try:
        from main import app
        from replication.region_manager import RegionStatus
        region_manager = app.state.region_manager
        
        if region_id not in region_manager.regions:
            raise HTTPException(status_code=404, detail="Region not found")
            
        region = region_manager.regions[region_id]
        region.status = RegionStatus.RECOVERING
        region.last_heartbeat = time.time()
        
        return {
            "status": "success",
            "message": f"Recovery initiated for region {region_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/recovery/all")
async def recover_all_regions():
    """Recover all failed regions"""
    try:
        from main import app
        from replication.region_manager import RegionStatus
        region_manager = app.state.region_manager
        
        recovered_count = 0
        for region in region_manager.regions.values():
            if region.status == RegionStatus.FAILED:
                region.status = RegionStatus.RECOVERING
                region.last_heartbeat = time.time()
                recovered_count += 1
        
        return {
            "status": "success",
            "message": f"Recovery initiated for {recovered_count} regions"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/system/status")
async def get_system_status():
    """Get overall system status"""
    from main import app
    health_monitor = app.state.health_monitor
    region_manager = app.state.region_manager
    replication_coordinator = app.state.replication_coordinator
    client_router = app.state.client_router
    
    health = await health_monitor.get_comprehensive_status()
    regions = region_manager.get_region_summary()
    replication = replication_coordinator.get_metrics()
    routing = client_router.get_routing_stats()
    
    return {
        "timestamp": time.time(),
        "overall_status": health["overall_status"],
        "regions": regions,
        "replication": replication,
        "routing": routing,
        "alerts": health["alerts"]
    }
