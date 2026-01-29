import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from src.scanner.ioc_database import IOCDatabase
from src.scanner.models import IOCIndicator, IOCType, Severity

@pytest.fixture
def mock_redis():
    redis_mock = Mock()
    redis_mock.setex = Mock(return_value=True)
    redis_mock.get = Mock(return_value=None)
    redis_mock.sadd = Mock(return_value=1)
    return redis_mock

@pytest.fixture
def ioc_db(mock_redis):
    return IOCDatabase(mock_redis, cache_ttl=3600)

def test_add_ioc(ioc_db):
    """Test adding IOC to database"""
    ioc = IOCIndicator(
        value="192.168.1.100",
        ioc_type=IOCType.IP_ADDRESS,
        severity=Severity.HIGH,
        source="test_feed",
        description="Test malicious IP"
    )
    
    result = ioc_db.add_ioc(ioc)
    assert result == True
    assert ioc_db.stats["total_iocs"] == 1

def test_lookup_ioc_not_found(ioc_db):
    """Test IOC lookup when not found"""
    result = ioc_db.lookup_ioc("10.0.0.1", IOCType.IP_ADDRESS)
    assert result is None

def test_batch_lookup(ioc_db):
    """Test batch IOC lookup"""
    values = [
        ("192.168.1.1", IOCType.IP_ADDRESS),
        ("evil.com", IOCType.DOMAIN)
    ]
    
    results = ioc_db.batch_lookup(values)
    assert isinstance(results, list)

def test_get_stats(ioc_db):
    """Test statistics retrieval"""
    stats = ioc_db.get_stats()
    assert "total_iocs" in stats
    assert "lookups" in stats
    assert "cache_hit_rate" in stats
