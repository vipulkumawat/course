import pytest
from datetime import datetime, timedelta
from src.query.influx_builder import InfluxQueryBuilder
from src.models import MetricQuery, TimeRange, AggregationWindow

@pytest.fixture
def query_builder():
    return InfluxQueryBuilder()

def test_flux_query_generation(query_builder):
    """Test Flux query string generation"""
    query = MetricQuery(
        measurement="http_requests",
        time_range=TimeRange(
            start=datetime(2025, 6, 15),
            end=datetime(2025, 6, 16)
        ),
        aggregation_window=AggregationWindow.HOUR
    )
    
    flux_query = query_builder.build_flux_query(query)
    assert "http_requests" in flux_query
    assert "aggregateWindow" in flux_query
    assert "1h" in flux_query

def test_query_with_filters(query_builder):
    """Test query with tag filters"""
    query = MetricQuery(
        measurement="http_requests",
        time_range=TimeRange(
            start=datetime(2025, 6, 15),
            end=datetime(2025, 6, 16)
        ),
        filters={"service": ["api", "web"]}
    )
    
    flux_query = query_builder.build_flux_query(query)
    assert 'service' in flux_query
    assert 'api' in flux_query or 'web' in flux_query
