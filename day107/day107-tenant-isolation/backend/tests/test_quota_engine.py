"""Tests for quota engine."""
import pytest
import asyncio
from core.quota_engine import QuotaEngine, ResourceQuota, QuotaViolationError

@pytest.fixture
def quota_engine():
    """Create quota engine for testing."""
    engine = QuotaEngine()
    quota = ResourceQuota(
        cpu_cores=2.0,
        memory_mb=1024,
        storage_mb=2048,
        requests_per_minute=100,
        concurrent_connections=10
    )
    engine.set_quota("test-tenant", quota)
    return engine

class TestQuotaEngine:
    """Test quota engine functionality."""
    
    @pytest.mark.asyncio
    async def test_quota_enforcement(self, quota_engine):
        """Test basic quota enforcement."""
        # Should allow within limits
        result = await quota_engine.allocate_resources("test-tenant", cpu=0.5, memory=256)
        assert result is True
        
        # Should prevent exceeding limits
        with pytest.raises(QuotaViolationError):
            await quota_engine.allocate_resources("test-tenant", cpu=3.0, memory=2048)
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, quota_engine):
        """Test request rate limiting."""
        # Record many requests
        for _ in range(150):  # Exceed limit of 100
            quota_engine.tracker.record_request("test-tenant")
        
        # Should block when rate exceeded
        result = await quota_engine.check_quota("test-tenant", "requests")
        assert result is False
    
    def test_quota_utilization(self, quota_engine):
        """Test quota utilization calculation."""
        # Record some requests
        for _ in range(50):
            quota_engine.tracker.record_request("test-tenant")
        
        utilization = quota_engine.get_quota_utilization("test-tenant")
        
        assert "cpu" in utilization
        assert "memory" in utilization
        assert "requests" in utilization
        assert utilization["requests"] == 50.0  # 50% of 100 requests/min
    
    def test_tenant_isolation_paths(self, quota_engine):
        """Test tenant filesystem isolation."""
        path = quota_engine.get_tenant_path("test-tenant")
        assert "test-tenant" in path
        assert path.startswith("data/tenant_data/")
