import pytest
import asyncio
import yaml
from unittest.mock import AsyncMock, MagicMock
from src.scaling.scaling_coordinator import ScalingCoordinator

@pytest.mark.asyncio
async def test_full_scaling_workflow():
    """Test complete scaling workflow from metrics to execution"""
    
    # Create test config
    test_config = {
        'monitoring': {
            'collection_interval': 1,
            'evaluation_interval': 2
        },
        'scaling_policies': {
            'test_component': {
                'min_instances': 1,
                'max_instances': 5,
                'target_cpu_utilization': 50
            }
        },
        'orchestration': {
            'health_check_timeout': 10
        }
    }
    
    # Save test config
    with open('test_config.yaml', 'w') as f:
        yaml.dump(test_config, f)
    
    try:
        coordinator = ScalingCoordinator('test_config.yaml')
        
        # Mock the orchestrator to avoid actual container operations
        coordinator.orchestrator.execute_scaling_decision = AsyncMock(return_value=True)
        
        await coordinator.initialize()
        
        # Simulate high CPU metrics
        test_metrics = {
            'test_component': type('ComponentMetrics', (), {
                'component_id': 'test_component',
                'component_type': 'test_component',
                'cpu_percent': 80.0,  # Above threshold
                'memory_percent': 60.0,
                'queue_depth': 500,
                'response_time_ms': 100.0,
                'instance_count': 1
            })()
        }
        
        # Mock metrics collector
        coordinator.metrics_collector.get_latest_metrics = MagicMock(return_value=test_metrics)
        
        # Run one evaluation cycle
        await coordinator._evaluate_and_scale()
        
        # Verify scaling decision was executed
        coordinator.orchestrator.execute_scaling_decision.assert_called_once()
        
        # Clean up
        coordinator.stop()
        
    finally:
        # Clean up test file
        import os
        if os.path.exists('test_config.yaml'):
            os.remove('test_config.yaml')

@pytest.mark.asyncio
async def test_metrics_collection():
    """Test metrics collection functionality"""
    from src.monitoring.metrics_collector import MetricsCollector
    
    config = {'collection_interval': 1}
    collector = MetricsCollector(config)
    
    await collector.register_component('test-comp', 'test_type')
    
    metrics = await collector.collect_system_metrics('test-comp')
    
    assert metrics.component_id == 'test-comp'
    assert metrics.component_type == 'test_type'
    assert metrics.cpu_percent >= 0
    assert metrics.memory_percent >= 0
