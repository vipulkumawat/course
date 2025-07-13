"""
Unit tests for Failure Injector
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from src.chaos.failure_injector import FailureInjector, FailureScenario, FailureType, create_failure_scenario


class TestFailureInjector:
    
    @pytest.fixture
    def mock_config(self):
        return {
            'safety_limits': {
                'max_blast_radius': 0.3,
                'max_concurrent_scenarios': 3,
                'max_severity': 4
            }
        }
    
    @pytest.fixture
    def failure_injector(self, mock_config):
        with patch('docker.from_env'), patch('src.chaos.failure_injector.subprocess'):
            injector = FailureInjector(mock_config)
            injector.docker_client = Mock()
            return injector
    
    def test_create_failure_scenario(self):
        """Test failure scenario creation"""
        scenario = create_failure_scenario(
            scenario_type="network_partition",
            target="test-container",
            parameters={"isolate_from": "172.17.0.0/16"},
            duration=300,
            severity=3
        )
        
        assert scenario.type == FailureType.NETWORK_PARTITION
        assert scenario.target == "test-container"
        assert scenario.duration == 300
        assert scenario.severity == 3
        assert scenario.status == "pending"
    
    def test_safety_check_blast_radius(self, failure_injector):
        """Test safety check for blast radius"""
        scenario = FailureScenario(
            id="test-1",
            type=FailureType.NETWORK_PARTITION,
            target="test-container",
            parameters={},
            blast_radius=0.5  # Exceeds limit
        )
        
        assert not failure_injector._safety_check(scenario)
    
    def test_safety_check_severity(self, failure_injector):
        """Test safety check for severity"""
        scenario = FailureScenario(
            id="test-2",
            type=FailureType.NETWORK_PARTITION,
            target="test-container",
            parameters={},
            severity=5  # Exceeds limit
        )
        
        assert not failure_injector._safety_check(scenario)
    
    def test_safety_check_concurrent_limit(self, failure_injector):
        """Test safety check for concurrent scenarios"""
        # Add 3 active scenarios
        for i in range(3):
            failure_injector.active_scenarios[f"test-{i}"] = Mock()
        
        scenario = FailureScenario(
            id="test-new",
            type=FailureType.NETWORK_PARTITION,
            target="test-container",
            parameters={}
        )
        
        assert not failure_injector._safety_check(scenario)
    
    @pytest.mark.asyncio
    async def test_inject_network_partition(self, failure_injector):
        """Test network partition injection"""
        mock_container = Mock()
        mock_container.id = "container123"
        failure_injector.docker_client.containers.get.return_value = mock_container
        
        scenario = FailureScenario(
            id="test-partition",
            type=FailureType.NETWORK_PARTITION,
            target="test-container",
            parameters={"isolate_from": "172.17.0.0/16"}
        )
        
        with patch('src.chaos.failure_injector.subprocess.run') as mock_subprocess:
            await failure_injector._inject_network_partition(scenario)
            
            # Verify subprocess calls were made
            assert mock_subprocess.call_count == 2  # Two iptables rules
            assert 'isolation_rules' in scenario.metadata
    
    @pytest.mark.asyncio
    async def test_inject_component_failure(self, failure_injector):
        """Test component failure injection"""
        mock_container = Mock()
        failure_injector.docker_client.containers.get.return_value = mock_container
        
        scenario = FailureScenario(
            id="test-crash",
            type=FailureType.COMPONENT_FAILURE,
            target="test-container",
            parameters={"mode": "crash"}
        )
        
        await failure_injector._inject_component_failure(scenario)
        
        # Verify container was stopped
        mock_container.stop.assert_called_once()
        assert scenario.metadata['action'] == 'stopped'
    
    @pytest.mark.asyncio
    async def test_recovery_network_partition(self, failure_injector):
        """Test recovery from network partition"""
        mock_container = Mock()
        mock_container.id = "container123"
        failure_injector.docker_client.containers.get.return_value = mock_container
        
        scenario = FailureScenario(
            id="test-recovery",
            type=FailureType.NETWORK_PARTITION,
            target="test-container",
            parameters={},
            metadata={
                'isolation_rules': [
                    "docker exec container123 iptables -A INPUT -s 172.17.0.0/16 -j DROP"
                ]
            }
        )
        
        with patch('src.chaos.failure_injector.subprocess.run') as mock_subprocess:
            await failure_injector._recover_network_partition(scenario)
            
            # Verify recovery rule was executed
            mock_subprocess.assert_called()
            call_args = mock_subprocess.call_args[0][0]
            assert '-D INPUT' in ' '.join(call_args)  # DELETE rule
    
    @pytest.mark.asyncio
    async def test_emergency_recovery(self, failure_injector):
        """Test emergency recovery functionality"""
        # Add mock active scenarios
        scenario1 = Mock()
        scenario1.id = "test-1"
        scenario2 = Mock()
        scenario2.id = "test-2"
        
        failure_injector.active_scenarios = {
            "test-1": scenario1,
            "test-2": scenario2
        }
        
        with patch.object(failure_injector, 'recover_failure', return_value=True) as mock_recover:
            result = await failure_injector.emergency_recovery()
            
            assert result is True
            assert mock_recover.call_count == 2
            mock_recover.assert_any_call("test-1")
            mock_recover.assert_any_call("test-2")
    
    def test_get_active_scenarios(self, failure_injector):
        """Test getting active scenarios"""
        import time
        
        scenario = FailureScenario(
            id="test-active",
            type=FailureType.NETWORK_PARTITION,
            target="test-container",
            parameters={},
            started_at=time.time()
        )
        
        failure_injector.active_scenarios["test-active"] = scenario
        
        active_list = failure_injector.get_active_scenarios()
        
        assert len(active_list) == 1
        assert active_list[0]['id'] == "test-active"
        assert active_list[0]['type'] == "network_partition"
        assert 'elapsed' in active_list[0]


if __name__ == "__main__":
    pytest.main([__file__])
