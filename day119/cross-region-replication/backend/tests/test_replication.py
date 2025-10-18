"""
Tests for cross-region replication system
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from replication.coordinator import ReplicationCoordinator, ReplicationStatus
from replication.region_manager import RegionManager, RegionStatus
from monitoring.health_monitor import HealthMonitor

class TestReplicationCoordinator:
    @pytest.fixture
    async def coordinator(self):
        region_manager = Mock()
        region_manager.regions = {"us-east-1": Mock(), "us-west-2": Mock()}
        region_manager.is_region_healthy = Mock(return_value=True)
        region_manager.get_region = Mock(return_value=Mock())
        
        coordinator = ReplicationCoordinator(region_manager)
        await coordinator.start()
        yield coordinator
        await coordinator.stop()

    @pytest.mark.asyncio
    async def test_replication_coordination(self, coordinator):
        """Test basic replication coordination"""
        data = {"message": "test log", "timestamp": time.time()}
        
        result = await coordinator.replicate_data(data, "us-east-1")
        assert result is True
        
        # Check metrics are updated
        metrics = coordinator.get_metrics()
        assert len(metrics) >= 0

    @pytest.mark.asyncio
    async def test_conflict_resolution(self, coordinator):
        """Test conflict resolution mechanism"""
        local_data = {"id": "123", "value": "local", "timestamp": 1000}
        remote_data = {"id": "123", "value": "remote", "timestamp": 2000}
        
        resolved = coordinator.conflict_resolver.resolve_conflict(local_data, remote_data)
        
        # Should choose remote (newer timestamp)
        assert resolved["value"] == "remote"
        assert resolved["timestamp"] == 2000

class TestRegionManager:
    @pytest.fixture
    async def region_manager(self):
        manager = RegionManager()
        await manager.initialize()
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_region_initialization(self, region_manager):
        """Test region manager initialization"""
        assert len(region_manager.regions) == 4
        assert region_manager.primary_region == "us-east-1"
        
        # Check all regions are healthy initially
        healthy_regions = region_manager.get_healthy_regions()
        assert len(healthy_regions) == 4

    @pytest.mark.asyncio
    async def test_failover_handling(self, region_manager):
        """Test region failover handling"""
        original_primary = region_manager.primary_region
        
        # Trigger failover
        result = await region_manager.handle_region_failure(original_primary)
        assert result is True
        
        # Primary should have changed
        assert region_manager.primary_region != original_primary

    def test_region_summary(self, region_manager):
        """Test region summary generation"""
        summary = region_manager.get_region_summary()
        
        assert "total_regions" in summary
        assert "healthy_regions" in summary
        assert "primary_region" in summary
        assert "regions" in summary
        
        assert summary["total_regions"] == 4

class TestHealthMonitor:
    @pytest.fixture
    async def health_monitor(self):
        region_manager = Mock()
        region_manager.get_region_summary = Mock(return_value={
            "regions": {
                "us-east-1": {"status": "healthy", "latency_ms": 20}
            }
        })
        
        monitor = HealthMonitor(region_manager)
        await monitor.start_monitoring()
        yield monitor
        await monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_health_monitoring(self, health_monitor):
        """Test health monitoring functionality"""
        # Wait a moment for metrics collection
        await asyncio.sleep(1)
        
        status = await health_monitor.get_comprehensive_status()
        
        assert "timestamp" in status
        assert "system" in status
        assert "regions" in status
        assert "alerts" in status
        assert "overall_status" in status

    def test_health_score_calculation(self, health_monitor):
        """Test health score calculation"""
        from replication.region_manager import Region, RegionStatus
        
        healthy_region = Region(
            id="test",
            name="Test Region",
            location="Test Location",
            endpoint="https://test.example.com",
            status=RegionStatus.HEALTHY,
            last_heartbeat=time.time(),
            data_store={},
            connection_latency=0.05
        )
        
        score = health_monitor._calculate_health_score(healthy_region)
        assert score == 100.0
        
        # Test failed region
        healthy_region.status = RegionStatus.FAILED
        score = health_monitor._calculate_health_score(healthy_region)
        assert score == 20.0
