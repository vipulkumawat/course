import asyncio
import logging
from datetime import datetime
from typing import List, Optional

import docker
from models.deployment import (
    DeploymentRequest, DeploymentStatus, DeploymentState, 
    Environment, HealthStatus
)
from core.health_checker import HealthChecker
from core.traffic_router import TrafficRouter

logger = logging.getLogger(__name__)

class DeploymentController:
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
            self.docker_available = True
            logger.info("✅ Docker client initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Docker client not available: {e}")
            self.docker_client = None
            self.docker_available = False
        
        self.current_state = DeploymentState.STABLE
        self.active_environment = Environment.BLUE
        self.deployment_history = []
        self.health_checker = HealthChecker()
        self.traffic_router = TrafficRouter()
        
    async def initialize_environments(self):
        """Initialize blue and green environments"""
        logger.info("🔧 Initializing blue and green environments")
        
        # Start blue environment (initially active)
        await self._start_environment(Environment.BLUE)
        
        # Start green environment (initially standby)
        await self._start_environment(Environment.GREEN)
        
        # Configure traffic router to point to blue
        await self.traffic_router.set_active_environment(Environment.BLUE)
        
        logger.info("✅ Environments initialized")
    
    async def deploy(self, deployment_request: DeploymentRequest) -> DeploymentStatus:
        """Execute blue/green deployment"""
        logger.info(f"🚀 Starting deployment: {deployment_request.version}")
        
        deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Set deployment state
            self.current_state = DeploymentState.DEPLOYING
            
            # Determine target environment
            target_env = Environment.GREEN if self.active_environment == Environment.BLUE else Environment.BLUE
            
            # Deploy to target environment
            await self._deploy_to_environment(target_env, deployment_request)
            
            # Health validation
            health_status = await self._validate_environment_health(target_env)
            
            if health_status.is_healthy:
                # Switch traffic
                await self._switch_traffic(target_env)
                
                # Update active environment
                self.active_environment = target_env
                self.current_state = DeploymentState.STABLE
                
                status = DeploymentStatus(
                    deployment_id=deployment_id,
                    state=DeploymentState.COMPLETED,
                    active_environment=self.active_environment,
                    version=deployment_request.version,
                    health_status=health_status,
                    message="Deployment completed successfully"
                )
            else:
                # Rollback on health check failure
                await self._rollback(target_env)
                
                status = DeploymentStatus(
                    deployment_id=deployment_id,
                    state=DeploymentState.FAILED,
                    active_environment=self.active_environment,
                    version=deployment_request.version,
                    health_status=health_status,
                    message="Deployment failed health checks, rolled back"
                )
            
            self.deployment_history.append(status)
            return status
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            self.current_state = DeploymentState.FAILED
            
            # Emergency rollback
            await self._emergency_rollback()
            
            return DeploymentStatus(
                deployment_id=deployment_id,
                state=DeploymentState.FAILED,
                active_environment=self.active_environment,
                message=f"Deployment failed: {str(e)}"
            )
    
    async def _start_environment(self, environment: Environment):
        """Start an environment container"""
        env_name = environment.value
        port = 8001 if environment == Environment.BLUE else 8002
        
        if not self.docker_available:
            logger.info(f"⚠️ Docker not available, skipping container management for {env_name}")
            return
        
        try:
            # Stop existing container if running
            try:
                container = self.docker_client.containers.get(f"log-processor-{env_name}")
                container.stop()
                container.remove()
            except docker.errors.NotFound:
                pass
            
            # Start new container
            container = self.docker_client.containers.run(
                "log-processor:latest",
                name=f"log-processor-{env_name}",
                ports={8000: port},
                environment={
                    "ENVIRONMENT": env_name.upper(),
                    "LOG_LEVEL": "INFO"
                },
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            logger.info(f"✅ Started {env_name} environment on port {port}")
            
        except Exception as e:
            logger.error(f"❌ Failed to start {env_name} environment: {e}")
            raise
    
    async def _deploy_to_environment(self, environment: Environment, request: DeploymentRequest):
        """Deploy new version to target environment"""
        logger.info(f"📦 Deploying version {request.version} to {environment.value}")
        
        if not self.docker_available:
            logger.info(f"⚠️ Docker not available, simulating deployment to {environment.value}")
            return
        
        # Build new image with version tag
        image_tag = f"log-processor:{request.version}"
        
        # In real implementation, this would build from source
        # For demo, we'll update container with new environment variables
        env_name = environment.value
        port = 8001 if environment == Environment.BLUE else 8002
        
        try:
            # Stop current container
            container = self.docker_client.containers.get(f"log-processor-{env_name}")
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            pass
        
        # Start with new configuration
        container = self.docker_client.containers.run(
            "log-processor:latest",
            name=f"log-processor-{env_name}",
            ports={8000: port},
            environment={
                "ENVIRONMENT": env_name.upper(),
                "VERSION": request.version,
                "LOG_LEVEL": "INFO",
                "NEW_FEATURE": request.config.get("new_feature", "disabled")
            },
            detach=True,
            restart_policy={"Name": "unless-stopped"}
        )
        
        # Wait for container to be ready
        await asyncio.sleep(10)
        
        logger.info(f"✅ Deployment to {env_name} completed")
    
    async def _validate_environment_health(self, environment: Environment) -> HealthStatus:
        """Validate environment health"""
        logger.info(f"🏥 Validating {environment.value} environment health")
        
        port = 8001 if environment == Environment.BLUE else 8002
        
        # Perform comprehensive health checks
        health_results = await self.health_checker.check_environment_health(
            f"http://localhost:{port}"
        )
        
        return health_results
    
    async def _switch_traffic(self, target_environment: Environment):
        """Switch traffic to target environment"""
        logger.info(f"🔄 Switching traffic to {target_environment.value}")
        
        await self.traffic_router.set_active_environment(target_environment)
        
        # Graceful traffic switch with delay
        await asyncio.sleep(5)
        
        logger.info(f"✅ Traffic switched to {target_environment.value}")
    
    async def _rollback(self, failed_environment: Environment):
        """Rollback failed deployment"""
        logger.info(f"⏪ Rolling back {failed_environment.value} environment")
        
        # Restart previous version on failed environment
        await self._start_environment(failed_environment)
        
        logger.info("✅ Rollback completed")
    
    async def _emergency_rollback(self):
        """Emergency rollback to stable state"""
        logger.warning("🚨 Executing emergency rollback")
        
        # Ensure active environment is healthy
        await self.traffic_router.set_active_environment(self.active_environment)
        self.current_state = DeploymentState.STABLE
        
        logger.info("✅ Emergency rollback completed")
    
    async def get_status(self) -> DeploymentStatus:
        """Get current deployment status"""
        health_status = await self.health_checker.get_overall_health()
        
        return DeploymentStatus(
            deployment_id="current",
            state=self.current_state,
            active_environment=self.active_environment,
            health_status=health_status,
            message="System operational"
        )
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up deployment controller")
        
        try:
            # Stop health monitoring
            self.health_checker.stop_monitoring()
            
            # Stop all containers
            for env_name in ["blue", "green"]:
                try:
                    container = self.docker_client.containers.get(f"log-processor-{env_name}")
                    container.stop()
                    container.remove()
                    logger.info(f"✅ Stopped {env_name} environment")
                except docker.errors.NotFound:
                    pass
                except Exception as e:
                    logger.error(f"❌ Failed to stop {env_name} environment: {e}")
            
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
