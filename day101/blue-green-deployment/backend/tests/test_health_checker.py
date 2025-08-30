import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.core.health_checker import HealthChecker

@pytest.fixture
def health_checker():
    return HealthChecker()

@pytest.mark.asyncio
async def test_http_health_check(health_checker):
    """Test HTTP health check"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await health_checker._check_http_health("http://localhost:8001")
        
        assert result.passed == True
        assert result.check_name == "http_health"

@pytest.mark.asyncio
async def test_performance_check(health_checker):
    """Test performance check"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await health_checker._check_performance("http://localhost:8001")
        
        assert result.check_name == "performance"
        assert "response_time_ms" in result.details

@pytest.mark.asyncio
async def test_resource_check(health_checker):
    """Test resource utilization check"""
    with patch('psutil.cpu_percent', return_value=50.0), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk:
        
        mock_memory.return_value.percent = 60.0
        mock_disk.return_value.percent = 70.0
        
        result = await health_checker._check_resources()
        
        assert result.passed == True
        assert result.check_name == "resources"
        assert result.details["cpu_percent"] == 50.0
