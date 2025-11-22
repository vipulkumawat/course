import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from unittest.mock import Mock, AsyncMock
from services.ticket_service import TicketService
from models.ticket import TicketRequest


@pytest.fixture
def ticket_service():
    service = TicketService()
    service.jira_client = Mock()
    service.servicenow_client = Mock()
    service.connected = True
    return service


@pytest.mark.asyncio
async def test_create_jira_ticket(ticket_service):
    """Test JIRA ticket creation"""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"key": "DEMO-123"}

    ticket_service.jira_client.post = AsyncMock(return_value=mock_response)

    request = TicketRequest(
        title="Test Database Error",
        description="Database connection timeout",
        system="JIRA",
        priority="2",
        category="database",
        team="database",
        source_event_id="event-123",
        fingerprint="abc123",
    )

    result = await ticket_service.create_ticket(request)
    assert result == "DEMO-123"
    ticket_service.jira_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_create_servicenow_ticket(ticket_service):
    """Test ServiceNow ticket creation"""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"result": {"number": "INC0012345"}}

    ticket_service.servicenow_client.post = AsyncMock(return_value=mock_response)

    request = TicketRequest(
        title="Infrastructure Alert",
        description="Server memory usage critical",
        system="ServiceNow",
        priority="1",
        category="infrastructure",
        team="infrastructure",
        source_event_id="event-456",
        fingerprint="def456",
    )

    result = await ticket_service.create_ticket(request)
    assert result == "INC0012345"
    ticket_service.servicenow_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_ticket_creation_failure(ticket_service):
    """Test handling of ticket creation failure"""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"

    ticket_service.jira_client.post = AsyncMock(return_value=mock_response)

    request = TicketRequest(
        title="Test Error",
        description="Test",
        system="JIRA",
        priority="3",
        category="test",
        team="test",
        source_event_id="event-789",
        fingerprint="ghi789",
    )

    result = await ticket_service.create_ticket(request)
    assert result is None
