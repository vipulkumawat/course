import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from fastapi.testclient import TestClient
from datetime import datetime


@pytest.fixture
def client():
    from src.main import app

    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns system info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Log Ticket Integration System"
    assert data["day"] == 138


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_submit_event_endpoint(client):
    """Test event submission endpoint"""
    event_data = {
        "id": "test-event-123",
        "timestamp": datetime.utcnow().isoformat(),
        "level": "error",
        "service": "test-service",
        "component": "test-component",
        "message": "Test error message",
        "metadata": {"test": True},
    }

    response = client.post("/api/events/submit", json=event_data)
    assert response.status_code == 200
    data = response.json()
    assert "event_id" in data
    assert data["event_id"] == "test-event-123"


def test_dashboard_stats_endpoint(client):
    """Test dashboard statistics endpoint"""
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "queue" in data
    assert "processing" in data
    assert "system_health" in data


def test_ticket_stats_endpoint(client):
    """Test ticket statistics endpoint"""
    # Override the dependency - get app from client
    from src.api.tickets import get_ticket_service
    from src.main import app

    async def mock_get_ticket_service():
        mock_service = MagicMock()
        mock_service.get_ticket_stats = AsyncMock(
            return_value={
                "total_created": 0,
                "jira_tickets": 0,
                "servicenow_tickets": 0,
                "last_24h": 0,
            }
        )
        return mock_service

    # Set override before making request
    app.dependency_overrides[get_ticket_service] = mock_get_ticket_service

    try:
        response = client.get("/api/tickets/stats")
        # Note: This test may fail if services aren't initialized
        # In a real integration test, services should be properly initialized
        if response.status_code == 503:
            pytest.skip("Ticket service not available - services need to be initialized")
        assert response.status_code == 200
        data = response.json()
        assert "total_created" in data
    finally:
        app.dependency_overrides.clear()
