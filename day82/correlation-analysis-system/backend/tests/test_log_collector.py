import pytest
import asyncio
from datetime import datetime
from src.collectors.log_collector import LogCollector, LogEvent

@pytest.mark.asyncio
async def test_log_collector_initialization():
    """Test log collector initialization"""
    collector = LogCollector()
    assert not collector.running
    assert collector.event_queue.qsize() == 0
    assert "web" in collector.sources
    assert "database" in collector.sources

@pytest.mark.asyncio
async def test_log_event_generation():
    """Test log event generation"""
    collector = LogCollector()
    
    # Test different source types
    for source in ["web", "database", "api", "payment", "inventory"]:
        event = collector._generate_log_event(source)
        assert event.source == source
        assert event.timestamp is not None
        assert event.level in ["INFO", "WARN", "ERROR"]
        assert event.message is not None

@pytest.mark.asyncio
async def test_event_queue_operations():
    """Test event queue operations"""
    collector = LogCollector()
    
    # Generate some events
    for _ in range(5):
        event = collector._generate_log_event("web")
        await collector.event_queue.put(event)
    
    # Get events
    events = await collector.get_events(3)
    assert len(events) == 3
    
    # Queue should still have events
    assert collector.event_queue.qsize() >= 2

def test_log_event_structure():
    """Test log event data structure"""
    collector = LogCollector()
    event = collector._generate_log_event("web")
    
    assert hasattr(event, 'timestamp')
    assert hasattr(event, 'source')
    assert hasattr(event, 'service')
    assert hasattr(event, 'level')
    assert hasattr(event, 'message')
    assert hasattr(event, 'metrics')
    
    # Web events should have specific metrics
    if event.source == "web":
        assert 'response_time' in event.metrics
        assert 'status_code' in event.metrics
