import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.dr_engine.dr_orchestrator import DROrchestrator
from src.replication.replication_engine import ReplicationEngine
from src.testing.chaos_engine import ChaosEngine, ChaosScenario

@pytest.fixture
def full_config():
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
            'batch_size': 100,
            'batch_timeout_ms': 100,
            'compression_enabled': True,
            'max_lag_ms': 500
        }
    }

@pytest.mark.asyncio
async def test_complete_dr_flow(full_config):
    # Initialize components
    orchestrator = DROrchestrator(full_config)
    await orchestrator.initialize_regions()
    
    replication = ReplicationEngine(full_config)
    await replication.start_replication('primary', 'secondary')
    
    chaos = ChaosEngine(orchestrator)
    
    # Let replication run
    await asyncio.sleep(2)
    
    # Run chaos test
    result = await chaos.run_scenario(ChaosScenario.NETWORK_PARTITION)
    
    assert result['passed'] == True
    assert result['rto_seconds'] < 120  # Within 2 minute RTO target
    assert result['rpo_seconds'] < 10   # Within acceptable RPO
    
    # Stop replication
    await replication.stop()

@pytest.mark.asyncio
async def test_replication_metrics(full_config):
    replication = ReplicationEngine(full_config)
    await replication.start_replication('primary', 'secondary')
    
    # Let it replicate
    await asyncio.sleep(3)
    
    metrics = replication.get_metrics()
    
    assert metrics['total_replicated'] > 0
    assert metrics['replication_lag_ms'] < 1000
    assert metrics['compression_ratio'] > 0
    
    await replication.stop()
