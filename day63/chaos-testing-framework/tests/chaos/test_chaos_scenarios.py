"""
Chaos scenario tests - actual failure injection tests
"""

import pytest
import asyncio
import docker
import time
from unittest.mock import Mock, patch

from src.chaos.failure_injector import FailureInjector, create_failure_scenario


class TestChaosScenarios:
    
    @pytest.fixture
    def chaos_config(self):
        return {
            'safety_limits': {
                'max_blast_radius': 0.5,
                'max_concurrent_scenarios': 5,
                'max_severity': 5
            }
        }
    
    @pytest.mark.asyncio
    async def test_network_partition_scenario(self, chaos_config):
        """Test network partition chaos scenario"""
        failure_injector = FailureInjector(chaos_config)
        
        scenario = create_failure_scenario(
            scenario_type="network_partition",
            target="test-target",
            parameters={
                "isolate_from": "172.17.0.0/16",
                "blast_radius": 0.1
            },
            duration=30,
            severity=2
        )
        
        # Mock Docker operations
        with patch('docker.from_env') as mock_docker, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_container = Mock()
            mock_container.id = "container123"
            mock_docker.return_value.containers.get.return_value = mock_container
            
            # Test injection
            success = await failure_injector.inject_failure(scenario)
            assert success
            
            # Verify iptables rules were applied
            assert mock_subprocess.call_count >= 2
            
            # Test recovery
            recovery_success = await failure_injector.recover_failure(scenario.id)
            assert recovery_success
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_scenario(self, chaos_config):
        """Test resource exhaustion chaos scenario"""
        failure_injector = FailureInjector(chaos_config)
        
        scenario = create_failure_scenario(
            scenario_type="resource_exhaustion",
            target="test-target",
            parameters={
                "cpu_limit": 50,
                "memory_limit": 256,
                "blast_radius": 0.15
            },
            duration=45,
            severity=3
        )
        
        with patch('docker.from_env') as mock_docker:
            mock_container = Mock()
            mock_docker.return_value.containers.get.return_value = mock_container
            
            # Test injection
            success = await failure_injector.inject_failure(scenario)
            assert success
            
            # Verify container limits were updated
            mock_container.update.assert_called_once()
            call_kwargs = mock_container.update.call_args[1]
            assert 'cpu_quota' in call_kwargs or 'mem_limit' in call_kwargs
            
            # Test recovery
            recovery_success = await failure_injector.recover_failure(scenario.id)
            assert recovery_success
            
            # Verify limits were reset
            assert mock_container.update.call_count == 2  # Once for limit, once for reset
    
    @pytest.mark.asyncio
    async def test_component_failure_scenario(self, chaos_config):
        """Test component failure chaos scenario"""
        failure_injector = FailureInjector(chaos_config)
        
        scenario = create_failure_scenario(
            scenario_type="component_failure",
            target="test-target",
            parameters={
                "mode": "crash",
                "blast_radius": 0.2
            },
            duration=60,
            severity=4
        )
        
        with patch('docker.from_env') as mock_docker:
            mock_container = Mock()
            mock_docker.return_value.containers.get.return_value = mock_container
            
            # Test crash injection
            success = await failure_injector.inject_failure(scenario)
            assert success
            
            # Verify container was stopped
            mock_container.stop.assert_called_once()
            assert scenario.metadata['action'] == 'stopped'
            
            # Test recovery
            recovery_success = await failure_injector.recover_failure(scenario.id)
            assert recovery_success
            
            # Verify container was restarted
            mock_container.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_latency_injection_scenario(self, chaos_config):
        """Test latency injection chaos scenario"""
        failure_injector = FailureInjector(chaos_config)
        
        scenario = create_failure_scenario(
            scenario_type="latency_injection",
            target="test-target",
            parameters={
                "latency_ms": 200,
                "blast_radius": 0.1
            },
            duration=30,
            severity=2
        )
        
        with patch('docker.from_env') as mock_docker, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_container = Mock()
            mock_container.id = "container123"
            mock_docker.return_value.containers.get.return_value = mock_container
            
            # Test injection
            success = await failure_injector.inject_failure(scenario)
            assert success
            
            # Verify tc command was executed
            mock_subprocess.assert_called()
            call_args = ' '.join(mock_subprocess.call_args[0][0])
            assert 'tc qdisc add' in call_args
            assert 'netem delay' in call_args
            assert '200ms' in call_args
            
            # Test recovery
            recovery_success = await failure_injector.recover_failure(scenario.id)
            assert recovery_success
    
    @pytest.mark.asyncio
    async def test_scenario_timeout_handling(self, chaos_config):
        """Test scenario timeout and automatic recovery"""
        failure_injector = FailureInjector(chaos_config)
        
        # Create short duration scenario
        scenario = create_failure_scenario(
            scenario_type="latency_injection",
            target="test-target",
            parameters={"latency_ms": 100},
            duration=1,  # Very short duration
            severity=1
        )
        
        with patch('docker.from_env') as mock_docker, \
             patch('subprocess.run'):
            
            mock_container = Mock()
            mock_container.id = "container123"
            mock_docker.return_value.containers.get.return_value = mock_container
            
            # Inject failure
            success = await failure_injector.inject_failure(scenario)
            assert success
            
            # Wait for timeout (simulated)
            await asyncio.sleep(0.1)
            
            # Verify scenario is still active initially
            active_scenarios = failure_injector.get_active_scenarios()
            assert len(active_scenarios) == 1
            
            # Manual recovery (simulating timeout handler)
            recovery_success = await failure_injector.recover_failure(scenario.id)
            assert recovery_success
    
    @pytest.mark.asyncio
    async def test_blast_radius_enforcement(self, chaos_config):
        """Test blast radius safety enforcement"""
        failure_injector = FailureInjector(chaos_config)
        
        # Create scenario with excessive blast radius
        scenario = create_failure_scenario(
            scenario_type="component_failure",
            target="test-target",
            parameters={
                "mode": "crash",
                "blast_radius": 0.8  # Exceeds safety limit
            },
            duration=60,
            severity=2
        )
        
        # This should fail safety check
        with patch('docker.from_env'):
            success = await failure_injector.inject_failure(scenario)
            assert not success
            
            # Verify no scenarios are active
            active_scenarios = failure_injector.get_active_scenarios()
            assert len(active_scenarios) == 0


if __name__ == "__main__":
    pytest.main([__file__])
