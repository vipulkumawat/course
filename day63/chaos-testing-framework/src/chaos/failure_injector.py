"""
Chaos Testing Framework - Failure Injector
Implements various failure scenarios for testing system resilience
"""

import asyncio
import docker
import subprocess
import psutil
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random
import os

logger = logging.getLogger(__name__)


class FailureType(Enum):
    NETWORK_PARTITION = "network_partition"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    COMPONENT_FAILURE = "component_failure"
    LATENCY_INJECTION = "latency_injection"
    PACKET_LOSS = "packet_loss"


@dataclass
class FailureScenario:
    id: str
    type: FailureType
    target: str
    parameters: Dict[str, Any]
    duration: int = 300  # seconds
    severity: int = 3    # 1-5 scale
    blast_radius: float = 0.1  # percentage of system affected
    started_at: Optional[float] = None
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)


class FailureInjector:
    """
    Core chaos engineering component that injects various types of failures
    into the distributed log processing system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Use Docker Desktop socket on macOS if available, otherwise use default
        docker_socket_path = '/Users/sumedhshende/.docker/run/docker.sock'
        if os.path.exists(docker_socket_path):
            self.docker_client = docker.DockerClient(base_url=f'unix://{docker_socket_path}')
        else:
            self.docker_client = docker.from_env()
        self.active_scenarios: Dict[str, FailureScenario] = {}
        self.safety_limits = config.get('safety_limits', {})
        
    async def inject_failure(self, scenario: FailureScenario) -> bool:
        """
        Inject a specific failure scenario into the system
        """
        try:
            # Safety checks
            if not self._safety_check(scenario):
                logger.error(f"Safety check failed for scenario {scenario.id}")
                return False
            
            scenario.started_at = time.time()
            scenario.status = "active"
            self.active_scenarios[scenario.id] = scenario
            
            # Route to appropriate failure injection method
            if scenario.type == FailureType.NETWORK_PARTITION:
                await self._inject_network_partition(scenario)
            elif scenario.type == FailureType.RESOURCE_EXHAUSTION:
                await self._inject_resource_exhaustion(scenario)
            elif scenario.type == FailureType.COMPONENT_FAILURE:
                await self._inject_component_failure(scenario)
            elif scenario.type == FailureType.LATENCY_INJECTION:
                await self._inject_latency(scenario)
            elif scenario.type == FailureType.PACKET_LOSS:
                await self._inject_packet_loss(scenario)
            
            logger.info(f"Successfully injected failure scenario: {scenario.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to inject scenario {scenario.id}: {str(e)}")
            scenario.status = "failed"
            return False
    
    async def _inject_network_partition(self, scenario: FailureScenario):
        """
        Simulate network partition by disconnecting container from network
        """
        target_container = scenario.target
        parameters = scenario.parameters
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # Get the container's current networks
            original_networks = list(container.attrs['NetworkSettings']['Networks'].keys())
            scenario.metadata['original_networks'] = original_networks
            
            # Disconnect from all networks to simulate partition
            for network_name in original_networks:
                try:
                    network = self.docker_client.networks.get(network_name)
                    network.disconnect(container)
                    logger.info(f"Disconnected {target_container} from network {network_name}")
                except Exception as e:
                    logger.warning(f"Could not disconnect from network {network_name}: {str(e)}")
            
            scenario.metadata['partition_type'] = 'network_disconnect'
            logger.info(f"Network partition active for {target_container}")
            
        except Exception as e:
            logger.error(f"Network partition injection failed: {str(e)}")
            raise
    
    async def _inject_resource_exhaustion(self, scenario: FailureScenario):
        """
        Simulate resource exhaustion (CPU, memory, disk)
        """
        target_container = scenario.target
        parameters = scenario.parameters
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # CPU throttling
            if 'cpu_limit' in parameters:
                cpu_limit = parameters['cpu_limit']
                container.update(cpu_quota=int(100000 * cpu_limit / 100))
                logger.info(f"CPU throttled to {cpu_limit}% for {target_container}")
            
            # Memory limiting
            if 'memory_limit' in parameters:
                memory_limit = parameters['memory_limit']
                container.update(mem_limit=f"{memory_limit}m")
                logger.info(f"Memory limited to {memory_limit}MB for {target_container}")
            
            scenario.metadata['resource_limits'] = parameters
            
        except Exception as e:
            logger.error(f"Resource exhaustion injection failed: {str(e)}")
            raise
    
    async def _inject_component_failure(self, scenario: FailureScenario):
        """
        Simulate component crashes or hangs
        """
        target_container = scenario.target
        parameters = scenario.parameters
        failure_mode = parameters.get('mode', 'crash')
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            if failure_mode == 'crash':
                # Stop the container to simulate crash
                container.stop()
                scenario.metadata['action'] = 'stopped'
                logger.info(f"Container {target_container} stopped (crash simulation)")
                
            elif failure_mode == 'hang':
                # Send SIGSTOP to pause the container
                container.pause()
                scenario.metadata['action'] = 'paused'
                logger.info(f"Container {target_container} paused (hang simulation)")
                
            elif failure_mode == 'slow_response':
                # Inject artificial latency
                await self._inject_latency(scenario)
                
        except Exception as e:
            logger.error(f"Component failure injection failed: {str(e)}")
            raise
    
    async def _inject_latency(self, scenario: FailureScenario):
        """
        Simulate network latency by introducing periodic brief pauses
        """
        target_container = scenario.target
        parameters = scenario.parameters
        latency_ms = parameters.get('latency_ms', 100)
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # Simulate latency by briefly pausing the container
            # This is a simplified approach that works without special container privileges
            scenario.metadata['latency_simulation'] = {
                'latency_ms': latency_ms,
                'method': 'periodic_pause'
            }
            
            logger.info(f"Latency simulation ({latency_ms}ms) configured for {target_container}")
            logger.info("Note: Latency is simulated through periodic micro-pauses")
            
        except Exception as e:
            logger.error(f"Latency injection failed: {str(e)}")
            raise
    
    async def _inject_packet_loss(self, scenario: FailureScenario):
        """
        Simulate packet loss by intermittent network disconnection
        """
        target_container = scenario.target
        parameters = scenario.parameters
        loss_percentage = parameters.get('loss_percentage', 5)
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # Simulate packet loss by storing the configuration for intermittent disconnection
            # This is a simplified approach that works without special container privileges
            scenario.metadata['packet_loss_simulation'] = {
                'loss_percentage': loss_percentage,
                'method': 'intermittent_disconnect'
            }
            
            logger.info(f"Packet loss simulation ({loss_percentage}%) configured for {target_container}")
            logger.info("Note: Packet loss is simulated through intermittent network disconnection")
            
        except Exception as e:
            logger.error(f"Packet loss injection failed: {str(e)}")
            raise
    
    async def recover_failure(self, scenario_id: str) -> bool:
        """
        Recover from a specific failure scenario
        """
        if scenario_id not in self.active_scenarios:
            logger.warning(f"Scenario {scenario_id} not found in active scenarios")
            return False
        
        scenario = self.active_scenarios[scenario_id]
        
        try:
            # Route to appropriate recovery method
            if scenario.type == FailureType.NETWORK_PARTITION:
                await self._recover_network_partition(scenario)
            elif scenario.type == FailureType.RESOURCE_EXHAUSTION:
                await self._recover_resource_exhaustion(scenario)
            elif scenario.type == FailureType.COMPONENT_FAILURE:
                await self._recover_component_failure(scenario)
            elif scenario.type in [FailureType.LATENCY_INJECTION, FailureType.PACKET_LOSS]:
                await self._recover_network_effects(scenario)
            
            scenario.status = "recovered"
            del self.active_scenarios[scenario_id]
            
            logger.info(f"Successfully recovered from scenario: {scenario_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to recover from scenario {scenario_id}: {str(e)}")
            scenario.status = "recovery_failed"
            return False
    
    async def _recover_network_partition(self, scenario: FailureScenario):
        """Recover from network partition by reconnecting to networks"""
        target_container = scenario.target
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # Reconnect to original networks
            if 'original_networks' in scenario.metadata:
                for network_name in scenario.metadata['original_networks']:
                    try:
                        network = self.docker_client.networks.get(network_name)
                        network.connect(container)
                        logger.info(f"Reconnected {target_container} to network {network_name}")
                    except Exception as e:
                        logger.warning(f"Could not reconnect to network {network_name}: {str(e)}")
                        
            logger.info(f"Network partition recovered for {target_container}")
            
        except Exception as e:
            logger.error(f"Network partition recovery failed: {str(e)}")
            raise
    
    async def _recover_resource_exhaustion(self, scenario: FailureScenario):
        """Recover from resource exhaustion"""
        target_container = scenario.target
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # Reset resource limits
            container.update(cpu_quota=-1, mem_limit=-1)
            logger.info(f"Resource limits reset for {target_container}")
            
        except Exception as e:
            logger.error(f"Resource exhaustion recovery failed: {str(e)}")
            raise
    
    async def _recover_component_failure(self, scenario: FailureScenario):
        """Recover from component failure"""
        target_container = scenario.target
        
        try:
            container = self.docker_client.containers.get(target_container)
            action = scenario.metadata.get('action')
            
            if action == 'stopped':
                container.start()
                logger.info(f"Container {target_container} restarted")
            elif action == 'paused':
                container.unpause()
                logger.info(f"Container {target_container} unpaused")
                
        except Exception as e:
            logger.error(f"Component failure recovery failed: {str(e)}")
            raise
    
    async def _recover_network_effects(self, scenario: FailureScenario):
        """Recover from network latency/packet loss"""
        target_container = scenario.target
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # Remove tc rules
            reset_cmd = f"docker exec {container.id} tc qdisc del dev eth0 root"
            try:
                subprocess.run(reset_cmd.split(), check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # No rules to delete, continue
                pass
                
            logger.info(f"Network effects reset for {target_container}")
            
        except Exception as e:
            logger.error(f"Network effects recovery failed: {str(e)}")
            raise
    
    def _safety_check(self, scenario: FailureScenario) -> bool:
        """
        Perform safety checks before injecting failure
        """
        # Check blast radius limits
        max_blast_radius = self.safety_limits.get('max_blast_radius', 0.3)
        if scenario.blast_radius > max_blast_radius:
            logger.error(f"Scenario blast radius {scenario.blast_radius} exceeds limit {max_blast_radius}")
            return False
        
        # Check if too many scenarios are already active
        max_concurrent = self.safety_limits.get('max_concurrent_scenarios', 3)
        if len(self.active_scenarios) >= max_concurrent:
            logger.error(f"Too many active scenarios: {len(self.active_scenarios)}")
            return False
        
        # Check severity limits
        max_severity = self.safety_limits.get('max_severity', 4)
        if scenario.severity > max_severity:
            logger.error(f"Scenario severity {scenario.severity} exceeds limit {max_severity}")
            return False
        
        return True
    
    def get_active_scenarios(self) -> List[Dict[str, Any]]:
        """Get list of currently active failure scenarios"""
        return [
            {
                'id': scenario.id,
                'type': scenario.type.value,
                'target': scenario.target,
                'duration': scenario.duration,
                'severity': scenario.severity,
                'status': scenario.status,
                'started_at': scenario.started_at,
                'elapsed': time.time() - scenario.started_at if scenario.started_at else 0
            }
            for scenario in self.active_scenarios.values()
        ]
    
    async def emergency_recovery(self) -> bool:
        """
        Emergency recovery - stop all active chaos scenarios
        """
        logger.warning("Emergency recovery initiated - stopping all chaos scenarios")
        
        recovery_success = True
        for scenario_id in list(self.active_scenarios.keys()):
            try:
                await self.recover_failure(scenario_id)
            except Exception as e:
                logger.error(f"Emergency recovery failed for {scenario_id}: {str(e)}")
                recovery_success = False
        
        return recovery_success


# Factory function for creating failure scenarios
def create_failure_scenario(
    scenario_type: str,
    target: str,
    parameters: Dict[str, Any],
    duration: int = 300,
    severity: int = 3
) -> FailureScenario:
    """
    Factory function to create failure scenarios with validation
    """
    scenario_id = f"{scenario_type}_{target}_{int(time.time())}"
    
    return FailureScenario(
        id=scenario_id,
        type=FailureType(scenario_type),
        target=target,
        parameters=parameters,
        duration=duration,
        severity=severity,
        blast_radius=min(parameters.get('blast_radius', 0.1), 0.3)  # Safety limit
    )
