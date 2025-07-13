"""
Integration tests for Chaos Testing Framework
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
import docker
import requests

from src.chaos.failure_injector import FailureInjector, create_failure_scenario
from src.monitoring.system_monitor import SystemMonitor
from src.recovery.recovery_validator import RecoveryValidator


class TestChaosIntegration:
    
    @pytest.fixture
    def config(self):
        return {
            'chaos_testing': {
                'safety_limits': {
                    'max_blast_radius': 0.3,
                    'max_concurrent_scenarios': 3,
                    'max_severity': 4
                }
            },
            'monitoring': {
                'redis_url': 'redis://localhost:6379',
                'monitored_services': ['test-service'],
                'alert_thresholds': []
            },
            'recovery': {}
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_chaos_scenario(self, config):
        """Test complete chaos scenario lifecycle"""
        # Initialize components
        failure_injector = FailureInjector(config['chaos_testing'])
        system_monitor = SystemMonitor(config['monitoring'])
        recovery_validator = RecoveryValidator(config['recovery'])
        
        # Mock Docker client
        with patch('docker.from_env') as mock_docker:
            mock_container = Mock()
            mock_container.id = "test123"
            mock_container.status = "running"
            mock_docker.return_value.containers.get.return_value = mock_container
            mock_docker.return_value.containers.list.return_value = [mock_container]
            
            # Create scenario
            scenario = create_failure_scenario(
                scenario_type="component_failure",
                target="test-container",
                parameters={"mode": "crash"},
                duration=60,
                severity=2
            )
            
            # Inject failure
            with patch('subprocess.run'):
                success = await failure_injector.inject_failure(scenario)
                assert success
                
                # Verify scenario is active
                active_scenarios = failure_injector.get_active_scenarios()
                assert len(active_scenarios) == 1
                assert active_scenarios[0]['status'] == 'active'
                
                # Wait a moment to simulate failure duration
                await asyncio.sleep(0.1)
                
                # Recover from failure
                recovery_success = await failure_injector.recover_failure(scenario.id)
                assert recovery_success
                
                # Verify no active scenarios
                active_scenarios = failure_injector.get_active_scenarios()
                assert len(active_scenarios) == 0
    
    @pytest.mark.asyncio
    async def test_monitoring_during_chaos(self, config):
        """Test monitoring functionality during chaos scenarios"""
        system_monitor = SystemMonitor(config['monitoring'])
        
        # Mock Redis connection
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            
            await system_monitor.initialize()
            
            # Mock system metrics
            with patch('psutil.cpu_percent', return_value=45.0), \
                 patch('psutil.virtual_memory') as mock_memory, \
                 patch('psutil.disk_usage') as mock_disk:
                
                mock_memory.return_value.percent = 60.0
                mock_disk.return_value.percent = 75.0
                
                # Collect metrics
                current_metrics = await system_monitor._monitor_system_metrics.__wrapped__(system_monitor)
                
                # Verify metrics were collected
                assert len(system_monitor.metrics_history) > 0
                latest_metrics = system_monitor.metrics_history[-1]
                assert latest_metrics.cpu_usage == 45.0
                assert latest_metrics.memory_usage == 60.0
                assert latest_metrics.disk_usage == 75.0
    
    @pytest.mark.asyncio
    async def test_recovery_validation(self, config):
        """Test recovery validation process"""
        recovery_validator = RecoveryValidator(config['recovery'])
        
        # Mock HTTP responses for service health checks
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 0.05
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Run recovery validation
            validation_report = await recovery_validator.validate_recovery("test-scenario-123")
            
            # Verify validation report structure
            assert 'scenario_id' in validation_report
            assert 'overall_success' in validation_report
            assert 'test_results' in validation_report
            assert 'summary' in validation_report
            
            assert validation_report['scenario_id'] == "test-scenario-123"
            assert isinstance(validation_report['overall_success'], bool)
            assert len(validation_report['test_results']) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_scenarios(self, config):
        """Test multiple concurrent chaos scenarios"""
        failure_injector = FailureInjector(config['chaos_testing'])
        
        # Mock Docker client
        with patch('docker.from_env') as mock_docker:
            mock_container = Mock()
            mock_container.id = "test123"
            mock_docker.return_value.containers.get.return_value = mock_container
            
            scenarios = []
            
            # Create multiple scenarios
            for i in range(2):
                scenario = create_failure_scenario(
                    scenario_type="latency_injection",
                    target=f"test-container-{i}",
                    parameters={"latency_ms": 100},
                    duration=60,
                    severity=1
                )
                scenarios.append(scenario)
            
            # Inject failures concurrently
            with patch('subprocess.run'):
                tasks = []
                for scenario in scenarios:
                    task = failure_injector.inject_failure(scenario)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                
                # Verify all scenarios were injected successfully
                assert all(results)
                
                # Verify scenarios are active
                active_scenarios = failure_injector.get_active_scenarios()
                assert len(active_scenarios) == 2
                
                # Recover all scenarios
                recovery_tasks = []
                for scenario in scenarios:
                    task = failure_injector.recover_failure(scenario.id)
                    recovery_tasks.append(task)
                
                recovery_results = await asyncio.gather(*recovery_tasks)
                assert all(recovery_results)


if __name__ == "__main__":
    pytest.main([__file__])
