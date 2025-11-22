import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from services.event_processor import EventProcessor
from models.log_event import LogEvent


@pytest.fixture
def mock_ticket_service():
    service = Mock()
    service.create_ticket = AsyncMock(return_value="TICKET-123")
    return service


@pytest.fixture
def event_processor(mock_ticket_service):
    processor = EventProcessor(mock_ticket_service)
    processor.redis = Mock()
    return processor


@pytest.mark.asyncio
async def test_process_critical_event(event_processor):
    """Test processing critical event creates ticket"""
    event = LogEvent(
        id="event-123",
        timestamp=datetime.utcnow(),
        level="critical",
        service="database",
        component="connection",
        message="Database server unavailable",
        metadata={"environment": "production"},
    )

    # Mock Redis operations
    event_processor.redis.get = AsyncMock(return_value=None)  # No existing ticket
    event_processor.redis.setex = AsyncMock()

    # Mock classification
    event_processor._classify_event = AsyncMock()
    event_processor._classify_event.return_value = Mock(should_create_ticket=True)

    # Mock ticket creation
    event_processor._create_ticket_request = AsyncMock()
    event_processor._create_ticket_request.return_value = Mock()

    result = await event_processor.process_event(event)
    assert result == "TICKET-123"


@pytest.mark.asyncio
async def test_process_info_event_no_ticket(event_processor):
    """Test info level event doesn't create ticket"""
    event = LogEvent(
        id="event-456",
        timestamp=datetime.utcnow(),
        level="info",
        service="web",
        component="handler",
        message="Request processed successfully",
        metadata={},
    )

    # Mock classification to not create ticket
    event_processor._classify_event = AsyncMock()
    event_processor._classify_event.return_value = Mock(should_create_ticket=False)

    result = await event_processor.process_event(event)
    assert result is None


def test_generate_fingerprint(event_processor):
    """Test fingerprint generation for deduplication"""
    event1 = LogEvent(
        id="event-1",
        timestamp=datetime.utcnow(),
        level="error",
        service="api",
        component="auth",
        message="Authentication failed for user 123",
        metadata={},
    )

    event2 = LogEvent(
        id="event-2",
        timestamp=datetime.utcnow(),
        level="error",
        service="api",
        component="auth",
        message="Authentication failed for user 456",  # Different user ID
        metadata={},
    )

    fingerprint1 = event_processor._generate_fingerprint(event1)
    fingerprint2 = event_processor._generate_fingerprint(event2)

    # Should be same fingerprint for similar errors
    assert fingerprint1 == fingerprint2
    assert len(fingerprint1) == 16  # SHA256 truncated to 16 chars
