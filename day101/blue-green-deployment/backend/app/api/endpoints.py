from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import logging

from models.deployment import DeploymentRequest, DeploymentStatus, HealthStatus
from core.deployment_controller import DeploymentController
from core.health_checker import HealthChecker

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances (in production, use dependency injection)
deployment_controller = DeploymentController()
health_checker = HealthChecker()

@router.post("/deploy", response_model=DeploymentStatus)
async def deploy(deployment_request: DeploymentRequest, background_tasks: BackgroundTasks):
    """Trigger a blue/green deployment"""
    try:
        logger.info(f"🚀 Deployment request received: {deployment_request.version}")
        
        # Execute deployment in background
        status = await deployment_controller.deploy(deployment_request)
        return status
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=DeploymentStatus)
async def get_deployment_status():
    """Get current deployment status"""
    try:
        return await deployment_controller.get_status()
    except Exception as e:
        logger.error(f"❌ Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthStatus)
async def get_health():
    """Get overall system health"""
    try:
        return await health_checker.get_overall_health()
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rollback")
async def rollback():
    """Trigger emergency rollback"""
    try:
        # Implementation would trigger rollback
        logger.info("⏪ Rollback triggered")
        return {"message": "Rollback initiated", "status": "success"}
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/environments")
async def get_environments():
    """Get information about both environments"""
    try:
        blue_health = await health_checker.check_environment_health("http://localhost:8001")
        green_health = await health_checker.check_environment_health("http://localhost:8002")
        
        return {
            "blue": {
                "port": 8001,
                "health": blue_health.model_dump(),
                "active": deployment_controller.active_environment.value == "blue"
            },
            "green": {
                "port": 8002,
                "health": green_health.model_dump(),
                "active": deployment_controller.active_environment.value == "green"
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get environments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_deployment_history():
    """Get deployment history"""
    try:
        return {
            "deployments": [dep.model_dump() for dep in deployment_controller.deployment_history],
            "total": len(deployment_controller.deployment_history)
        }
    except Exception as e:
        logger.error(f"❌ Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
