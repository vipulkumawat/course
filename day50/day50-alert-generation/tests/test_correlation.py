"""Tests for correlation engine."""
import pytest
import asyncio
from datetime import datetime
from src.correlation.engine import CorrelationEngine
from config.database import LogEntry, get_db, Alert

@pytest.fixture
def correlation_engine():
    return CorrelationEngine()

@pytest.mark.asyncio
async def test_alert_correlation(correlation_engine):
    """Test alert correlation functionality."""
    # Clean up any existing test data
    db = next(get_db())
    try:
        db.query(Alert).filter(Alert.pattern_name == 'test_pattern').delete()
        db.commit()
    finally:
        db.close()
    
    # Create a pattern match
    pattern_match = {
        'pattern_name': 'test_pattern',
        'severity': 'high',
        'threshold': 3,
        'window': 300,
        'log_entry': LogEntry(
            message="Test error message",
            level="ERROR",
            source="test_service"
        )
    }
    
    # First correlation should create new alert
    alert1 = await correlation_engine.correlate_alert(pattern_match)
    assert alert1 is not None
    assert alert1['count'] == 1
    assert alert1['state'] == 'NEW'
    
    # Second correlation should update existing alert
    alert2 = await correlation_engine.correlate_alert(pattern_match)
    assert alert2['id'] == alert1['id']
    assert alert2['count'] == 2

@pytest.mark.asyncio
async def test_rate_limiting(correlation_engine):
    """Test alert rate limiting."""
    # Should not suppress first alert
    result1 = await correlation_engine.suppress_duplicate_alerts("test_pattern")
    assert result1 == False
    
    # Simulate reaching rate limit
    correlation_engine.active_correlations["test_pattern_" + str(int(datetime.utcnow().timestamp() // 60))] = [datetime.utcnow()] * 15
    
    # Should suppress additional alerts
    result2 = await correlation_engine.suppress_duplicate_alerts("test_pattern")
    assert result2 == True
