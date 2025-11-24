import pytest
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.src.models.webhook import Base, WebhookEndpoint, WebhookDelivery
from backend.src.core.webhook_engine import WebhookEngine

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

@pytest.fixture
def sample_endpoint(db_session):
    endpoint = WebhookEndpoint(
        name="Test Slack Webhook",
        url="https://hooks.slack.com/test",
        method="POST",
        auth_type="none",
        payload_template=json.dumps({
            "text": "Alert: {{message}}",
            "username": "Log Processor",
            "channel": "#alerts"
        }),
        event_filters=[
            {"field": "level", "operator": "equals", "value": "error"}
        ]
    )
    db_session.add(endpoint)
    db_session.commit()
    return endpoint

@pytest.mark.asyncio
async def test_webhook_creation_and_filtering(db_session, sample_endpoint):
    """Test webhook endpoint creation and event filtering"""
    engine = WebhookEngine(db_session)
    
    # Test matching event
    matching_event = {
        "type": "log_event",
        "timestamp": datetime.utcnow().isoformat(),
        "level": "error",
        "message": "Database connection failed",
        "source": "api_service"
    }
    
    delivery_ids = await engine.process_event(matching_event)
    assert len(delivery_ids) == 1
    
    # Test non-matching event
    non_matching_event = {
        "type": "log_event",
        "timestamp": datetime.utcnow().isoformat(),
        "level": "info",
        "message": "Request processed successfully",
        "source": "api_service"
    }
    
    delivery_ids = await engine.process_event(non_matching_event)
    assert len(delivery_ids) == 0

def test_filter_matching_logic(db_session):
    """Test event filter matching logic"""
    engine = WebhookEngine(db_session)
    
    event_data = {
        "level": "error",
        "response_time": 1500,
        "service": "payment-api"
    }
    
    # Test equals filter
    equals_filter = [{"field": "level", "operator": "equals", "value": "error"}]
    assert engine._matches_filters(event_data, equals_filter) == True
    
    # Test contains filter
    contains_filter = [{"field": "service", "operator": "contains", "value": "payment"}]
    assert engine._matches_filters(event_data, contains_filter) == True
    
    # Test greater_than filter
    gt_filter = [{"field": "response_time", "operator": "greater_than", "value": "1000"}]
    assert engine._matches_filters(event_data, gt_filter) == True

@pytest.mark.asyncio
async def test_payload_transformation(db_session, sample_endpoint):
    """Test webhook payload transformation"""
    engine = WebhookEngine(db_session)
    
    event_data = {
        "type": "error_event",
        "timestamp": "2025-05-20T10:30:00Z",
        "level": "error",
        "message": "Payment processing failed",
        "source": "payment_service",
        "metadata": {"user_id": "12345", "amount": 99.99}
    }
    
    delivery_id = await engine._create_delivery(sample_endpoint, event_data)
    
    # Verify delivery was created
    delivery = db_session.query(WebhookDelivery).filter(
        WebhookDelivery.id == delivery_id
    ).first()
    
    assert delivery is not None
    assert delivery.endpoint_id == sample_endpoint.id
    
    # Verify payload transformation
    payload = json.loads(delivery.payload)
    assert payload["text"] == "Alert: Payment processing failed"
    assert payload["username"] == "Log Processor"
    assert payload["channel"] == "#alerts"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
