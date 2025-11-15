import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, patch, Mock

from src.collectors.system_metrics import SystemMetricsCollector, SystemMetrics

@pytest_asyncio.fixture
async def redis_client():
    mock_redis = AsyncMock()
    mock_redis.hset = AsyncMock()
    mock_redis.expire = AsyncMock()
    return mock_redis

@pytest.mark.asyncio
async def test_metrics_collection(redis_client):
    """Test system metrics collection"""
    collector = SystemMetricsCollector(redis_client, collection_interval=1)
    
    with patch('psutil.cpu_percent', return_value=45.5), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_io_counters', return_value=Mock(read_bytes=1000, write_bytes=2000)), \
         patch('psutil.net_io_counters', return_value=Mock(bytes_sent=3000, bytes_recv=4000)), \
         patch('psutil.getloadavg', return_value=(1.0, 1.5, 2.0)):
        
        mock_memory.return_value.percent = 67.8
        
        metrics = await collector._collect_metrics()
        
        assert isinstance(metrics, SystemMetrics)
        assert metrics.cpu_percent == 45.5
        assert metrics.memory_percent == 67.8
        assert metrics.load_average == (1.0, 1.5, 2.0)

@pytest.mark.asyncio
async def test_metrics_storage(redis_client):
    """Test metrics storage in Redis"""
    collector = SystemMetricsCollector(redis_client)
    
    metrics = SystemMetrics(
        timestamp=1234567890.0,
        cpu_percent=55.5,
        memory_percent=70.0,
        disk_io={'read_bytes': 1000},
        network_io={'bytes_sent': 2000},
        load_average=(1.0, 1.5, 2.0)
    )
    
    await collector._store_metrics(metrics)
    
    # Verify Redis operations
    redis_client.hset.assert_called_once()
    redis_client.expire.assert_called_once_with("metrics:1234567890", 86400)

@pytest.mark.asyncio
async def test_collection_loop_start_stop():
    """Test collector start/stop functionality"""
    redis_client = AsyncMock()
    collector = SystemMetricsCollector(redis_client, collection_interval=0.1)
    
    # Start collection
    task = asyncio.create_task(collector.start_collection())
    await asyncio.sleep(0.05)  # Let it run briefly
    
    # Stop collection
    collector.stop()
    await asyncio.sleep(0.15)  # Wait for graceful shutdown
    
    assert not collector.running
    task.cancel()
    
    try:
        await task
    except asyncio.CancelledError:
        pass
