import pytest
import asyncio
import tempfile
import os
from datetime import datetime
from app.services.facet_engine import FacetEngine
from app.models.log_entry import LogEntry

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def facet_engine(temp_db):
    return FacetEngine(redis_url="redis://localhost:6379", db_path=temp_db)

@pytest.mark.asyncio
async def test_extract_facets(facet_engine):
    log = LogEntry(
        id="test-1",
        timestamp=datetime.now(),
        service="test-api",
        level="error",
        message="Test message",
        region="us-west-2",
        response_time=250
    )
    
    facets = await facet_engine.extract_facets(log)
    
    assert facets['service'] == 'test-api'
    assert facets['level'] == 'error'
    assert facets['region'] == 'us-west-2'
    assert facets['response_time_range'] == '100-500ms'

@pytest.mark.asyncio 
async def test_index_log(facet_engine):
    log = LogEntry(
        id="test-index-1",
        timestamp=datetime.now(),
        service="payment-api",
        level="info",
        message="Payment processed",
        region="us-east-1",
        response_time=50
    )
    
    await facet_engine.index_log(log)
    
    # Verify log was stored
    facets_summary = await facet_engine.get_facets()
    assert facets_summary.total_logs >= 1

@pytest.mark.asyncio
async def test_get_facets(facet_engine):
    # Index some test logs
    logs = [
        LogEntry(
            id=f"test-{i}",
            timestamp=datetime.now(),
            service="api" if i % 2 == 0 else "worker",
            level="info" if i % 3 == 0 else "error",
            message=f"Test message {i}",
            region="us-west-2",
            response_time=100 + i * 10
        )
        for i in range(5)
    ]
    
    for log in logs:
        await facet_engine.index_log(log)
    
    facets_summary = await facet_engine.get_facets()
    
    assert facets_summary.total_logs >= 5
    assert len(facets_summary.facets) > 0
    
    # Check that service facet exists
    service_facet = next((f for f in facets_summary.facets if f.name == 'service'), None)
    assert service_facet is not None
    assert len(service_facet.values) >= 1

if __name__ == "__main__":
    pytest.main([__file__])
