import pytest
import asyncio
from datetime import datetime, timedelta
from src.correlation.engine import CorrelationEngine, CorrelationResult
from src.collectors.log_collector import LogEvent

@pytest.mark.asyncio
async def test_correlation_engine_initialization():
    """Test correlation engine initialization"""
    engine = CorrelationEngine(window_seconds=30)
    assert engine.window_seconds == 30
    assert engine.correlations == []
    assert not engine.running

@pytest.mark.asyncio
async def test_temporal_correlation_detection():
    """Test temporal correlation detection"""
    engine = CorrelationEngine(window_seconds=30)
    
    # Create test events with same correlation_id
    base_time = datetime.now()
    event1 = LogEvent(
        timestamp=base_time,
        source="web",
        service="nginx",
        level="INFO",
        message="User login",
        correlation_id="test_123"
    )
    
    event2 = LogEvent(
        timestamp=base_time + timedelta(seconds=10),
        source="database",
        service="postgresql",
        level="INFO",
        message="User query",
        correlation_id="test_123"
    )
    
    correlations = await engine._find_temporal_correlations([event1, event2])
    
    assert len(correlations) > 0
    assert correlations[0].correlation_type == "session_based"
    assert correlations[0].strength > 0.5

@pytest.mark.asyncio
async def test_error_cascade_correlation():
    """Test error cascade correlation detection"""
    engine = CorrelationEngine(window_seconds=30)
    
    base_time = datetime.now()
    error1 = LogEvent(
        timestamp=base_time,
        source="api",
        service="checkout",
        level="ERROR",
        message="Payment failed"
    )
    
    error2 = LogEvent(
        timestamp=base_time + timedelta(seconds=5),
        source="database",
        service="postgresql",
        level="ERROR",
        message="Connection timeout"
    )
    
    correlations = await engine._find_temporal_correlations([error1, error2])
    
    assert len(correlations) > 0
    error_correlations = [c for c in correlations if c.correlation_type == "error_cascade"]
    assert len(error_correlations) > 0

@pytest.mark.asyncio
async def test_correlation_stats():
    """Test correlation statistics calculation"""
    engine = CorrelationEngine()
    
    # Add mock correlations
    engine.correlations = [
        CorrelationResult(
            event_a={}, event_b={}, correlation_type="session_based",
            strength=0.8, confidence=0.9, timestamp=datetime.now(), window_seconds=30
        ),
        CorrelationResult(
            event_a={}, event_b={}, correlation_type="error_cascade",
            strength=0.6, confidence=0.7, timestamp=datetime.now(), window_seconds=30
        )
    ]
    
    stats = await engine.get_correlation_stats()
    
    assert stats["total"] == 2
    assert "session_based" in stats["types"]
    assert "error_cascade" in stats["types"]
    assert stats["avg_strength"] > 0
