import pytest
from unittest.mock import Mock
from src.matcher.matcher_engine import IOCMatcherEngine
from src.scanner.ioc_database import IOCDatabase
from src.scanner.models import IOCIndicator, IOCType, Severity

@pytest.fixture
def mock_ioc_db():
    db = Mock(spec=IOCDatabase)
    db.batch_lookup = Mock(return_value=[])
    return db

@pytest.fixture
def matcher(mock_ioc_db):
    return IOCMatcherEngine(mock_ioc_db, max_workers=2)

def test_extract_ips(matcher):
    """Test IP extraction from logs"""
    log = {"message": "Connection from 192.168.1.100 detected"}
    iocs = matcher.extract_iocs_from_log(log)
    
    assert len(iocs) > 0
    assert any(ioc[1] == IOCType.IP_ADDRESS for ioc in iocs)

def test_extract_domains(matcher):
    """Test domain extraction from logs"""
    log = {"url": "http://malicious-site.com/payload"}
    iocs = matcher.extract_iocs_from_log(log)
    
    assert len(iocs) > 0
    assert any(ioc[1] == IOCType.DOMAIN for ioc in iocs)

def test_scan_log_no_matches(matcher, mock_ioc_db):
    """Test log scanning with no IOC matches"""
    log = {"message": "Normal log entry"}
    alerts = matcher.scan_log(log)
    
    assert isinstance(alerts, list)
    assert matcher.stats["logs_scanned"] > 0

def test_get_stats(matcher):
    """Test matcher statistics"""
    stats = matcher.get_stats()
    assert "logs_scanned" in stats
    assert "matches_found" in stats
