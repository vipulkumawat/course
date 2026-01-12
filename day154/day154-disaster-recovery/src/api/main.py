from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import yaml
import structlog
from typing import Dict
import json

from src.dr_engine.dr_orchestrator import DROrchestrator
from src.replication.replication_engine import ReplicationEngine
from src.testing.chaos_engine import ChaosEngine, ChaosScenario

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

app = FastAPI(title="Disaster Recovery System", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
dr_orchestrator = None
replication_engine = None
chaos_engine = None
config = None

@app.on_event("startup")
async def startup_event():
    """Initialize DR system on startup"""
    global dr_orchestrator, replication_engine, chaos_engine, config
    
    # Load configuration
    with open('config/dr_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize DR orchestrator
    dr_orchestrator = DROrchestrator(config['disaster_recovery'])
    await dr_orchestrator.initialize_regions()
    
    # Initialize replication engine
    replication_engine = ReplicationEngine(config['disaster_recovery'])
    await replication_engine.start_replication('primary', 'secondary')
    
    # Initialize chaos engine
    chaos_engine = ChaosEngine(dr_orchestrator)
    
    # Start monitoring loop
    asyncio.create_task(monitoring_loop())
    
    logger.info("DR System started successfully")

async def monitoring_loop():
    """Background monitoring loop"""
    while True:
        try:
            # Check for failures
            failed_region = await dr_orchestrator.detect_failure()
            
            if failed_region and config['disaster_recovery']['failover']['automatic']:
                logger.warning(f"Automatic failover triggered for {failed_region}")
                await dr_orchestrator.execute_failover(failed_region)
                
        except Exception as e:
            logger.error("Monitoring error", error=str(e))
            
        await asyncio.sleep(config['disaster_recovery']['health_checks']['interval_seconds'])

@app.get("/api/status")
async def get_status():
    """Get current DR system status"""
    return {
        'status': 'operational',
        'primary_region': dr_orchestrator.current_primary,
        'regions': {
            name: {
                'status': region['status'].value,
                'role': region['role'].value
            }
            for name, region in dr_orchestrator.regions.items()
        }
    }

@app.get("/api/metrics")
async def get_metrics():
    """Get DR and replication metrics"""
    dr_metrics = dr_orchestrator.get_metrics()
    replication_metrics = replication_engine.get_metrics()
    
    # Update replication lag in DR orchestrator
    for region_name in dr_orchestrator.regions:
        if region_name != dr_orchestrator.current_primary:
            dr_orchestrator.regions[region_name]['replication_lag_ms'] = \
                replication_metrics['replication_lag_ms']
    
    return {
        'dr_metrics': dr_metrics,
        'replication_metrics': replication_metrics,
        'rto_target_seconds': config['disaster_recovery']['rto_target_seconds'],
        'rpo_target_seconds': config['disaster_recovery']['rpo_target_seconds']
    }

@app.get("/api/failover-history")
async def get_failover_history():
    """Get failover history"""
    return {
        'history': dr_orchestrator.failover_history,
        'total_count': len(dr_orchestrator.failover_history)
    }

@app.post("/api/trigger-failover")
async def trigger_manual_failover():
    """Manually trigger failover"""
    if not dr_orchestrator.current_primary:
        return {'error': 'No primary region available'}
        
    result = await dr_orchestrator.execute_failover(dr_orchestrator.current_primary)
    return result

@app.post("/api/chaos/run/{scenario}")
async def run_chaos_test(scenario: str):
    """Run a chaos engineering test"""
    try:
        scenario_enum = ChaosScenario(scenario)
        result = await chaos_engine.run_scenario(scenario_enum)
        return result
    except ValueError:
        return {'error': f'Invalid scenario: {scenario}'}

@app.get("/api/chaos/results")
async def get_chaos_results():
    """Get chaos test results"""
    return {
        'results': chaos_engine.get_test_results(),
        'total_tests': len(chaos_engine.get_test_results())
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send current metrics
            metrics = await get_metrics()
            await websocket.send_json(metrics)
            await asyncio.sleep(2)
            
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
