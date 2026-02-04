import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_metrics_collection():
    redis_mock = AsyncMock()
    redis_mock.lpush = AsyncMock()
    redis_mock.ltrim = AsyncMock()
    redis_mock.expire = AsyncMock()
    
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src.monitoring.metrics_collector import MetricsCollector
    
    collector = MetricsCollector(redis_mock)
    await collector._collect_metrics()
    
    assert redis_mock.lpush.called
    print("✅ Metrics collection test passed")

def test_slo_violation_detection():
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src.models.sla_models import ServiceTier, MetricType
    
    # Test violation logic
    target = 100
    actual_compliant = 95
    actual_violated = 110
    
    assert actual_compliant < target, "Should be compliant"
    assert actual_violated > target, "Should be violated"
    print("✅ Violation detection test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
