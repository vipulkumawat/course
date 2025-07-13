"""
Chaos Testing Framework - Web Interface
FastAPI backend for chaos testing dashboard
"""

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
import uvicorn

from ..chaos.failure_injector import FailureInjector, create_failure_scenario, FailureType
from ..monitoring.system_monitor import SystemMonitor
from ..recovery.recovery_validator import RecoveryValidator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Chaos Testing Framework",
    description="Distributed Log Processing Chaos Testing Dashboard",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "ws://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
failure_injector: Optional[FailureInjector] = None
system_monitor: Optional[SystemMonitor] = None
recovery_validator: Optional[RecoveryValidator] = None
config: Dict[str, Any] = {}

# WebSocket connections for real-time updates
active_websockets: List[WebSocket] = []


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global failure_injector, system_monitor, recovery_validator, config
    
    try:
        # Load configuration
        with open('config/chaos_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Initialize components
        failure_injector = FailureInjector(config['chaos_testing'])
        system_monitor = SystemMonitor(config['monitoring'])
        recovery_validator = RecoveryValidator(config['recovery'])
        
        # Initialize system monitor
        await system_monitor.initialize()
        
        # Start background monitoring
        asyncio.create_task(system_monitor.start_monitoring())
        
        logger.info("Chaos testing framework initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize chaos testing framework: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if system_monitor:
        await system_monitor.stop_monitoring()
    
    if failure_injector:
        await failure_injector.emergency_recovery()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Chaos experiment endpoints
@app.post("/api/chaos/scenarios")
async def create_chaos_scenario(scenario_data: Dict[str, Any]):
    """Create and start a new chaos scenario"""
    try:
        scenario = create_failure_scenario(
            scenario_type=scenario_data['type'],
            target=scenario_data['target'],
            parameters=scenario_data.get('parameters', {}),
            duration=scenario_data.get('duration', 300),
            severity=scenario_data.get('severity', 3)
        )
        
        success = await failure_injector.inject_failure(scenario)
        
        if success:
            # Notify WebSocket clients
            await broadcast_update({
                'type': 'scenario_started',
                'scenario': {
                    'id': scenario.id,
                    'type': scenario.type.value,
                    'target': scenario.target,
                    'status': scenario.status
                }
            })
            
            return {"success": True, "scenario_id": scenario.id}
        else:
            raise HTTPException(status_code=400, detail="Failed to inject failure scenario")
            
    except Exception as e:
        logger.error(f"Error creating chaos scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chaos/scenarios")
async def get_active_scenarios():
    """Get list of active chaos scenarios"""
    try:
        scenarios = failure_injector.get_active_scenarios()
        return {"scenarios": scenarios}
    except Exception as e:
        logger.error(f"Error getting active scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chaos/scenarios/{scenario_id}/stop")
async def stop_chaos_scenario(scenario_id: str):
    """Stop a specific chaos scenario"""
    try:
        success = await failure_injector.recover_failure(scenario_id)
        
        if success:
            # Notify WebSocket clients
            await broadcast_update({
                'type': 'scenario_stopped',
                'scenario_id': scenario_id
            })
            
            return {"success": True, "message": f"Scenario {scenario_id} stopped successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop scenario")
            
    except Exception as e:
        logger.error(f"Error stopping scenario {scenario_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chaos/emergency-stop")
async def emergency_stop():
    """Emergency stop all chaos scenarios"""
    try:
        success = await failure_injector.emergency_recovery()
        
        if success:
            await broadcast_update({
                'type': 'emergency_stop_completed'
            })
            
            return {"success": True, "message": "Emergency stop completed"}
        else:
            raise HTTPException(status_code=500, detail="Emergency stop failed")
            
    except Exception as e:
        logger.error(f"Error during emergency stop: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Recovery validation endpoints
@app.post("/api/recovery/validate/{scenario_id}")
async def validate_recovery(scenario_id: str, background_tasks: BackgroundTasks):
    """Start recovery validation for a scenario"""
    try:
        # Run validation in background
        background_tasks.add_task(run_recovery_validation, scenario_id)
        
        return {"success": True, "message": f"Recovery validation started for {scenario_id}"}
        
    except Exception as e:
        logger.error(f"Error starting recovery validation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_recovery_validation(scenario_id: str):
    """Run recovery validation in background"""
    try:
        validation_report = await recovery_validator.validate_recovery(scenario_id)
        
        # Notify WebSocket clients
        await broadcast_update({
            'type': 'recovery_validation_completed',
            'scenario_id': scenario_id,
            'report': validation_report
        })
        
    except Exception as e:
        logger.error(f"Recovery validation error: {str(e)}")
        await broadcast_update({
            'type': 'recovery_validation_failed',
            'scenario_id': scenario_id,
            'error': str(e)
        })


# Monitoring endpoints
@app.get("/api/monitoring/metrics")
async def get_current_metrics():
    """Get current system metrics"""
    try:
        current_metrics = system_monitor.get_current_metrics()
        
        if current_metrics:
            return {
                "timestamp": current_metrics.timestamp,
                "cpu_usage": current_metrics.cpu_usage,
                "memory_usage": current_metrics.memory_usage,
                "disk_usage": current_metrics.disk_usage,
                "network_latency": current_metrics.network_latency,
                "service_health": current_metrics.service_health,
                "custom_metrics": current_metrics.custom_metrics
            }
        else:
            return {"message": "No metrics available"}
            
    except Exception as e:
        logger.error(f"Error getting current metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/summary")
async def get_metrics_summary(duration_minutes: int = 10):
    """Get metrics summary over specified duration"""
    try:
        summary = system_monitor.get_metrics_summary(duration_minutes)
        return summary
    except Exception as e:
        logger.error(f"Error getting metrics summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Configuration endpoints
@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return config


@app.get("/api/config/scenarios")
async def get_scenario_templates():
    """Get available scenario templates"""
    templates = [
        {
            "id": "network_partition",
            "name": "Network Partition",
            "description": "Simulate network partition between services",
            "type": "network_partition",
            "parameters": {
                "isolate_from": "172.17.0.0/16"
            },
            "targets": ["log-collector-service", "message-queue-service", "log-processor-service"]
        },
        {
            "id": "resource_exhaustion",
            "name": "Resource Exhaustion",
            "description": "Simulate CPU/memory pressure",
            "type": "resource_exhaustion",
            "parameters": {
                "cpu_limit": 50,
                "memory_limit": 256
            },
            "targets": ["log-collector-service", "log-processor-service"]
        },
        {
            "id": "component_failure",
            "name": "Component Failure",
            "description": "Simulate service crashes",
            "type": "component_failure",
            "parameters": {
                "mode": "crash"
            },
            "targets": ["log-collector-service", "message-queue-service", "log-processor-service"]
        },
        {
            "id": "latency_injection",
            "name": "Latency Injection",
            "description": "Add network latency",
            "type": "latency_injection",
            "parameters": {
                "latency_ms": 200
            },
            "targets": ["log-collector-service", "message-queue-service"]
        }
    ]
    
    return {"templates": templates}


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            # Send periodic updates
            current_metrics = None
            active_scenarios = []
            
            try:
                if system_monitor:
                    current_metrics = system_monitor.get_current_metrics()
                if failure_injector:
                    active_scenarios = failure_injector.get_active_scenarios()
            except Exception as e:
                logger.error(f"Error getting updates for WebSocket: {str(e)}")
            
            update = {
                'type': 'periodic_update',
                'metrics': {
                    "timestamp": current_metrics.timestamp,
                    "cpu_usage": current_metrics.cpu_usage,
                    "memory_usage": current_metrics.memory_usage,
                    "disk_usage": current_metrics.disk_usage,
                    "network_latency": current_metrics.network_latency,
                    "service_health": current_metrics.service_health,
                    "custom_metrics": current_metrics.custom_metrics
                } if current_metrics else {},
                'scenarios': active_scenarios
            }
            
            await websocket.send_text(json.dumps(update))
            await asyncio.sleep(5)  # Send updates every 5 seconds
            
    except Exception as e:
        logger.info(f"WebSocket disconnected: {str(e)}")
    finally:
        if websocket in active_websockets:
            active_websockets.remove(websocket)


async def broadcast_update(update: Dict[str, Any]):
    """Broadcast update to all connected WebSocket clients"""
    if active_websockets:
        message = json.dumps(update)
        disconnected = []
        
        for websocket in active_websockets:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.append(websocket)
        
        # Remove disconnected WebSockets
        for websocket in disconnected:
            active_websockets.remove(websocket)


# Test endpoints for demo
@app.post("/api/logs")
async def submit_log(log_data: Dict[str, Any]):
    """Submit a log entry (for testing purposes)"""
    # Simulate log processing
    await asyncio.sleep(0.01)  # Simulate processing time
    return {"success": True, "log_id": f"log_{int(datetime.now().timestamp())}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
