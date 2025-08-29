import asyncio
import logging
import docker
import time
from typing import Dict, List, Optional
from src.policies.policy_engine import ScalingDecision, ScalingAction

class ContainerOrchestrator:
    def __init__(self, config: Dict):
        self.config = config
        self.docker_client = docker.from_env()
        self.container_registry = {}
        self.health_check_timeout = config.get('health_check_timeout', 120)
        
    async def execute_scaling_decision(self, decision: ScalingDecision) -> bool:
        """Execute a scaling decision"""
        try:
            if decision.action == ScalingAction.SCALE_UP:
                return await self._scale_up(decision)
            elif decision.action == ScalingAction.SCALE_DOWN:
                return await self._scale_down(decision)
            return True
            
        except Exception as e:
            logging.error(f"Failed to execute scaling decision for {decision.component_id}: {e}")
            return False
    
    async def _scale_up(self, decision: ScalingDecision) -> bool:
        """Scale up a component by adding instances"""
        component_id = decision.component_id
        instances_to_add = decision.target_instances - decision.current_instances
        
        logging.info(f"Scaling up {component_id}: adding {instances_to_add} instances")
        
        for i in range(instances_to_add):
            container_name = f"{component_id}-{int(time.time())}-{i}"
            
            # Simulate container creation with different images based on component type
            image_name = self._get_image_name(decision.component_id)
            
            try:
                # In a real implementation, this would create actual containers
                # For demo purposes, we'll simulate the process
                await self._simulate_container_creation(container_name, image_name)
                
                if await self._health_check(container_name):
                    self._register_container(component_id, container_name)
                    logging.info(f"Successfully created and health-checked {container_name}")
                else:
                    logging.error(f"Health check failed for {container_name}")
                    return False
                    
            except Exception as e:
                logging.error(f"Failed to create container {container_name}: {e}")
                return False
        
        return True
    
    async def _scale_down(self, decision: ScalingDecision) -> bool:
        """Scale down a component by removing instances"""
        component_id = decision.component_id
        instances_to_remove = decision.current_instances - decision.target_instances
        
        logging.info(f"Scaling down {component_id}: removing {instances_to_remove} instances")
        
        containers = self._get_containers_for_component(component_id)
        containers_to_remove = containers[:instances_to_remove]
        
        for container_name in containers_to_remove:
            try:
                await self._graceful_shutdown(container_name)
                self._unregister_container(component_id, container_name)
                logging.info(f"Successfully removed {container_name}")
                
            except Exception as e:
                logging.error(f"Failed to remove container {container_name}: {e}")
                return False
        
        return True
    
    async def _simulate_container_creation(self, container_name: str, image_name: str):
        """Simulate container creation process"""
        # Simulate the time it takes to pull image and start container
        await asyncio.sleep(2)
        logging.info(f"Simulated creation of container {container_name} with image {image_name}")
    
    async def _health_check(self, container_name: str) -> bool:
        """Perform health check on a container"""
        # Simulate health check process
        await asyncio.sleep(1)
        
        # Simulate 95% success rate for health checks
        import random
        return random.random() < 0.95
    
    async def _graceful_shutdown(self, container_name: str):
        """Gracefully shutdown a container"""
        await asyncio.sleep(1)
        logging.info(f"Gracefully shut down {container_name}")
    
    def _get_image_name(self, component_id: str) -> str:
        """Get the appropriate Docker image for a component"""
        if 'processor' in component_id:
            return "log-processor:latest"
        elif 'collector' in component_id:
            return "log-collector:latest"
        elif 'storage' in component_id:
            return "log-storage:latest"
        return "log-generic:latest"
    
    def _register_container(self, component_id: str, container_name: str):
        """Register a container in the registry"""
        if component_id not in self.container_registry:
            self.container_registry[component_id] = []
        self.container_registry[component_id].append(container_name)
    
    def _unregister_container(self, component_id: str, container_name: str):
        """Unregister a container from the registry"""
        if component_id in self.container_registry:
            if container_name in self.container_registry[component_id]:
                self.container_registry[component_id].remove(container_name)
    
    def _get_containers_for_component(self, component_id: str) -> List[str]:
        """Get all containers for a component"""
        return self.container_registry.get(component_id, [])
    
    def get_component_instance_count(self, component_id: str) -> int:
        """Get current instance count for a component"""
        return len(self.container_registry.get(component_id, []))
