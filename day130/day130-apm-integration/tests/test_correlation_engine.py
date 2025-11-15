import pytest
import pytest_asyncio
import asyncio
import redis.asyncio as redis
from unittest.mock import AsyncMock, Mock
import json
import time

from src.correlation.engine import CorrelationEngine, EnrichedLog

@pytest_asyncio.fixture
async def redis_client():
    # Mock Redis client
    mock_redis = AsyncMock()
    mock_redis.hgetall = AsyncMock(return_value={
        b'cpu': b'75.5',
        b'memory': b'60.2',
        b'load_1': b'1.5'
    })
    mock_redis.set = AsyncMock()
    mock_redis.lpush = AsyncMock()
    mock_redis.expire = AsyncMock()
    return mock_redis

@pytest.fixture
def correlation_config():
    return {
        'correlation': {
            'window_size_seconds': 30,
            'threshold_cpu': 80.0,
            'threshold_memory': 75.0,
        },
        'alerts': {
            'cpu_critical': 90.0,
            'memory_critical': 85.0
        }
    }

@pytest.mark.asyncio
async def test_process_log_entry(redis_client, correlation_config):
    """Test processing a log entry with correlation"""
    engine = CorrelationEngine(redis_client, correlation_config)
    
    log_entry = {
        'timestamp': time.time(),
        'level': 'ERROR',
        'message': 'Database connection failed',
        'service': 'api'
    }
    
    enriched_log = await engine.process_log_entry(log_entry)
    
    assert isinstance(enriched_log, EnrichedLog)
    assert enriched_log.original_log == log_entry
    assert enriched_log.enhancement_level in ['NORMAL', 'HIGH', 'CRITICAL']
    assert enriched_log.correlation_id.startswith('corr_')

@pytest.mark.asyncio
async def test_enhancement_level_critical(redis_client, correlation_config):
    """Test critical enhancement level calculation"""
    # Mock high CPU metrics - return same data for all timestamp calls
    high_metrics = {
        b'cpu': b'85.0',
        b'memory': b'80.0'
    }
    redis_client.hgetall = AsyncMock(return_value=high_metrics)
    
    engine = CorrelationEngine(redis_client, correlation_config)
    
    log_entry = {
        'timestamp': time.time(),
        'level': 'ERROR',
        'message': 'System overload'
    }
    
    enriched_log = await engine.process_log_entry(log_entry)
    # CPU=85.0 > 80 and memory=80.0 > 75, with ERROR level should be CRITICAL
    assert enriched_log.enhancement_level == 'CRITICAL', f"Expected CRITICAL, got {enriched_log.enhancement_level}. Metrics context: {enriched_log.metrics_context}"

@pytest.mark.asyncio
async def test_metrics_context_aggregation(redis_client, correlation_config):
    """Test metrics context aggregation"""
    engine = CorrelationEngine(redis_client, correlation_config)
    
    log_entry = {
        'timestamp': time.time(),
        'level': 'INFO',
        'message': 'Request processed'
    }
    
    enriched_log = await engine.process_log_entry(log_entry)
    
    # Verify metrics context is populated
    assert 'cpu_avg' in enriched_log.metrics_context
    assert 'memory_avg' in enriched_log.metrics_context
    assert enriched_log.metrics_context['cpu_avg'] == 75.5

def test_calculate_enhancement_level():
    """Test enhancement level calculation logic"""
    engine = CorrelationEngine(None, {'alerts': {}})
    
    # Test critical level
    metrics = {'cpu_avg': 85.0, 'memory_avg': 80.0}
    log_entry = {'level': 'ERROR'}
    level = engine._calculate_enhancement_level(metrics, log_entry)
    assert level == 'CRITICAL'
    
    # Test high level
    metrics = {'cpu_avg': 65.0, 'memory_avg': 65.0}
    log_entry = {'level': 'WARNING'}
    level = engine._calculate_enhancement_level(metrics, log_entry)
    assert level == 'HIGH'
    
    # Test normal level
    metrics = {'cpu_avg': 30.0, 'memory_avg': 40.0}
    log_entry = {'level': 'INFO'}
    level = engine._calculate_enhancement_level(metrics, log_entry)
    assert level == 'NORMAL'
