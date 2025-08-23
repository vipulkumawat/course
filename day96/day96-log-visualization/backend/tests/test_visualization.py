import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.services.chart_service import ChartDataService
from src.models.log_models import TimeSeriesData, HeatmapData, DashboardMetrics

@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    session = Mock()
    
    # Mock query results for error trends
    mock_error_results = [
        Mock(service='api-gateway', hour='2025-05-16 10:00:00', total_logs=100, error_count=5),
        Mock(service='user-service', hour='2025-05-16 10:00:00', total_logs=80, error_count=2),
    ]
    
    # Mock query results for heatmap - hour should be an integer
    mock_heatmap_results = [
        Mock(service='api-gateway', hour=10, avg_response_time=125.5),
        Mock(service='user-service', hour=10, avg_response_time=89.3),
    ]
    
    # Mock query results for service performance - ensure numeric values
    mock_performance_results = [
        Mock(service='api-gateway', total_requests=1250, avg_response_time=125.5, error_count=26),
        Mock(service='user-service', total_requests=980, avg_response_time=89.3, error_count=15),
    ]
    
    def mock_query(*args):
        # Create a mock query object
        query_mock = Mock()
        
        # Mock the filter method
        def mock_filter(*filter_args):
            query_mock.filter_called = True
            return query_mock
        
        # Mock the group_by method
        def mock_group_by(*group_args):
            query_mock.group_by_called = True
            return query_mock
        
        # Mock the all method
        def mock_all():
            # Check if this is a heatmap query (has extract function)
            if any('extract' in str(arg) for arg in args):
                return mock_heatmap_results
            # Check if this is a service performance query (has count, avg, and sum)
            elif any('count' in str(arg) and 'avg' in str(arg) and 'sum' in str(arg) for arg in args):
                return mock_performance_results
            # Default case for error trends
            return mock_error_results
        
        # Mock the scalar method
        def mock_scalar():
            # Check if this is a count query
            if any('count' in str(arg) for arg in args):
                return 1000
            # Check if this is an avg query
            elif any('avg' in str(arg) for arg in args):
                return 150.0
            # Check if this is a distinct count query
            elif any('distinct' in str(arg) for arg in args):
                return 5
            return 0
        
        # Attach the mock methods
        query_mock.filter = mock_filter
        query_mock.group_by = mock_group_by
        query_mock.all = mock_all
        query_mock.scalar = mock_scalar
        
        return query_mock
    
    session.query = mock_query
    
    return session

@pytest.mark.asyncio
async def test_error_rate_trends(mock_db_session):
    """Test error rate trends calculation"""
    service = ChartDataService(mock_db_session)
    
    result = await service.get_error_rate_trends(hours=24)
    
    assert isinstance(result, list)
    assert len(result) >= 0
    if result:
        assert isinstance(result[0], TimeSeriesData)
        assert result[0].series_name is not None
        assert result[0].chart_type == "line"

@pytest.mark.asyncio
async def test_response_time_heatmap(mock_db_session):
    """Test response time heatmap generation"""
    service = ChartDataService(mock_db_session)
    
    result = await service.get_response_time_heatmap(hours=24)
    
    assert isinstance(result, HeatmapData)
    assert isinstance(result.x_labels, list)
    assert isinstance(result.y_labels, list)
    assert isinstance(result.values, list)
    assert len(result.values) >= 0

@pytest.mark.asyncio
async def test_service_performance_bars(mock_db_session):
    """Test service performance bar chart data"""
    service = ChartDataService(mock_db_session)
    
    result = await service.get_service_performance_bars(hours=1)
    
    assert isinstance(result, list)
    if result:
        assert 'service' in result[0]
        assert 'requests' in result[0]
        assert 'avg_response_time' in result[0]
        assert 'error_rate' in result[0]

@pytest.mark.asyncio
async def test_real_time_metrics(mock_db_session):
    """Test real-time metrics calculation"""
    service = ChartDataService(mock_db_session)
    
    result = await service.get_real_time_metrics()
    
    assert isinstance(result, DashboardMetrics)
    assert result.total_logs >= 0
    assert result.error_rate >= 0
    assert result.avg_response_time >= 0
    assert result.active_services >= 0

def test_chart_data_service_initialization(mock_db_session):
    """Test chart data service initialization"""
    service = ChartDataService(mock_db_session)
    assert service.db == mock_db_session
