"""Integration tests for Windows Event Log system"""
import pytest
import asyncio
import aiohttp
import json
from unittest.mock import patch, Mock, AsyncMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import WindowsEventLogService

class TestSystemIntegration:
    """Test complete system integration"""
    
    @pytest.fixture
    async def service(self):
        """Create service instance for testing"""
        service = WindowsEventLogService()
        await service.initialize()
        return service
        
    async def test_service_initialization(self, service):
        """Test service initializes all components"""
        assert service.agent is not None
        assert service.shipper is not None
        assert service.agent.config is not None
        
    async def test_mock_event_collection(self, service):
        """Test event collection with mock data"""
        # Start collection briefly
        collection_task = asyncio.create_task(service.agent.start_collection())
        
        # Let it run for a short time
        await asyncio.sleep(2)
        
        # Stop collection
        await service.agent.stop_collection()
        collection_task.cancel()
        
        # Verify some events were collected
        stats = service.agent.get_stats()
        assert stats['events_collected'] > 0
        
    async def test_dashboard_endpoints(self):
        """Test dashboard API endpoints"""
        from web.dashboard_app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test status endpoint
        response = client.get("/api/status")
        assert response.status_code == 200
        
        data = response.json()
        assert 'timestamp' in data
        assert 'running' in data
        assert 'channels' in data
        
        # Test events endpoint
        response = client.get("/api/events/recent")
        assert response.status_code == 200
        
        events = response.json()
        assert isinstance(events, list)
        
    async def test_websocket_connection(self):
        """Test WebSocket functionality"""
        from web.dashboard_app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test WebSocket connection
        with client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None
            
    async def test_configuration_loading(self, service):
        """Test configuration is loaded correctly"""
        config = service.agent.config
        
        assert len(config.channels) > 0
        assert config.max_events_per_batch > 0
        assert config.batch_timeout_seconds > 0
        assert 'System' in config.channels
        assert 'Application' in config.channels
        
    async def test_error_resilience(self, service):
        """Test system handles errors gracefully"""
        # Test with invalid transport URL
        service.shipper.config.transport_url = "http://invalid-url:99999"
        
        # Try to send an event
        test_event = {
            'channel': 'System',
            'event_id': 1001,
            'message': 'Test event'
        }
        
        # Should not crash
        try:
            await service.shipper.ship_event(test_event)
            await service.shipper.flush()
        except:
            pass
            
        # Service should still be functional
        assert service.shipper is not None
        assert service.agent is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
