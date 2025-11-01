"""Integration tests for CloudWatch collector."""
import pytest
import time
from src.collector.orchestrator import CloudWatchCollector


@pytest.mark.integration
def test_collector_lifecycle():
    """Test collector start/stop lifecycle."""
    collector = CloudWatchCollector('config/config.yaml')
    
    # Start collector
    collector.start()
    time.sleep(2)
    
    # Verify it's running
    assert collector.running is True
    
    # Stop collector
    collector.stop()
    assert collector.running is False
