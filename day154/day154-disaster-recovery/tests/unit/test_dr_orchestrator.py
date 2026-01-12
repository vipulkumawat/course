import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.dr_engine.dr_orchestrator import DROrchestrator, RegionStatus, RegionRole

@pytest.fixture
def dr_config():
    return {
        'regions': {
            'primary': {
                'name': 'us-east-1',
                'host': 'localhost',
                'port': 8001,
                'role': 'primary'
            },
            'secondary': {
                'name': 'us-west-2',
                'host': 'localhost',
                'port': 8002,
                'role': 'secondary'
            }
        },
        'health_checks': {
            'interval_seconds': 10,
            'timeout_seconds': 5,
            'failure_threshold': 3
        },
        'failover': {
            'automatic': True,
            'validation_timeout_seconds': 60,
            'cooldown_seconds': 300
        },
        'replication': {
            'max_lag_ms': 500
        }
    }

@pytest.mark.asyncio
async def test_initialize_regions(dr_config):
    orchestrator = DROrchestrator(dr_config)
    await orchestrator.initialize_regions()
    
    assert len(orchestrator.regions) == 2
    assert orchestrator.current_primary == 'primary'
    assert orchestrator.regions['primary']['role'] == RegionRole.PRIMARY

@pytest.mark.asyncio
async def test_failover_execution(dr_config):
    orchestrator = DROrchestrator(dr_config)
    await orchestrator.initialize_regions()
    
    # Simulate failure
    result = await orchestrator.execute_failover('primary')
    
    assert result['status'] == 'success'
    assert result['to_region'] == 'secondary'
    assert orchestrator.current_primary == 'secondary'
    assert result['rto_seconds'] > 0

def test_metrics_tracking(dr_config):
    orchestrator = DROrchestrator(dr_config)
    
    metrics = orchestrator.get_metrics()
    assert 'total_failovers' in metrics
    assert 'average_rto_seconds' in metrics
    assert metrics['total_failovers'] == 0
