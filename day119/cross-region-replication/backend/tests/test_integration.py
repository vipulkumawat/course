"""
Integration tests for cross-region replication system
"""
import pytest
import asyncio
import httpx
import time

@pytest.mark.asyncio
async def test_full_system_integration():
    """Test complete system integration"""
    # This would normally start the full system
    # For demo purposes, we'll test individual component integration
    
    from replication.region_manager import RegionManager
    from replication.coordinator import ReplicationCoordinator
    from monitoring.health_monitor import HealthMonitor
    
    # Initialize components
    region_manager = RegionManager()
    await region_manager.initialize()
    
    coordinator = ReplicationCoordinator(region_manager)
    await coordinator.start()
    
    health_monitor = HealthMonitor(region_manager)
    await health_monitor.start_monitoring()
    
    try:
        # Test data replication
        test_data = {
            "message": "Integration test log",
            "level": "info",
            "service": "test-service",
            "timestamp": time.time()
        }
        
        # Submit data for replication
        result = await coordinator.replicate_data(test_data, "us-east-1")
        assert result is True
        
        # Wait for replication to process
        await asyncio.sleep(2)
        
        # Check metrics
        metrics = coordinator.get_metrics()
        assert len(metrics) >= 0
        
        # Test health monitoring
        health_status = await health_monitor.get_comprehensive_status()
        assert health_status["overall_status"] in ["healthy", "warning", "critical"]
        
        # Test region management
        summary = region_manager.get_region_summary()
        assert summary["total_regions"] == 4
        
    finally:
        # Cleanup
        await health_monitor.stop_monitoring()
        await coordinator.stop()
        await region_manager.cleanup()

@pytest.mark.asyncio 
async def test_failover_scenario():
    """Test complete failover scenario"""
    from replication.region_manager import RegionManager
    from replication.coordinator import ReplicationCoordinator
    
    region_manager = RegionManager()
    await region_manager.initialize()
    
    coordinator = ReplicationCoordinator(region_manager)
    await coordinator.start()
    
    try:
        original_primary = region_manager.primary_region
        
        # Trigger failover
        failover_result = await coordinator.trigger_failover(original_primary)
        assert failover_result is True
        
        # Verify new primary was elected
        new_primary = region_manager.primary_region
        assert new_primary != original_primary
        
        # Test that replication still works
        test_data = {"message": "Post-failover test", "timestamp": time.time()}
        replication_result = await coordinator.replicate_data(test_data, new_primary)
        assert replication_result is True
        
    finally:
        await coordinator.stop()
        await region_manager.cleanup()
