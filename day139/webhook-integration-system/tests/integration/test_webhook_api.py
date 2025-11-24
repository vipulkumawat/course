import pytest
import json
import asyncio
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.src.api.main import app, get_db
from backend.src.models.webhook import Base, WebhookEndpoint, WebhookDelivery

@pytest.fixture(scope="function")
def test_db():
    # Import Base and models to ensure they're registered with Base.metadata
    from backend.src.models.webhook import Base, WebhookEndpoint, WebhookDelivery
    
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    try:
        # Create database engine using the temporary file
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        
        # Create all tables - models must be imported first
        Base.metadata.create_all(bind=engine)
        
        # Create session factory bound to the same engine
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create a generator function that matches the get_db signature
        def get_test_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        yield get_test_db
    finally:
        # Clean up the temporary database file
        if os.path.exists(db_path):
            os.unlink(db_path)

@pytest.fixture
def client(test_db):
    app.dependency_overrides[get_db] = test_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_create_webhook_endpoint(client):
    """Test webhook endpoint creation via API"""
    webhook_data = {
        "name": "Test Slack Integration",
        "url": "https://hooks.slack.com/services/test",
        "method": "POST",
        "auth_type": "none",
        "payload_template": json.dumps({
            "text": "{{message}}",
            "channel": "#alerts"
        }),
        "event_filters": [
            {"field": "level", "operator": "equals", "value": "error"}
        ]
    }
    
    response = client.post("/api/webhooks", json=webhook_data)
    assert response.status_code == 200
    assert "id" in response.json()

def test_get_webhooks(client):
    """Test webhook listing via API"""
    # First create a webhook
    webhook_data = {
        "name": "Test Webhook",
        "url": "https://example.com/webhook",
        "method": "POST",
        "auth_type": "none"
    }
    
    client.post("/api/webhooks", json=webhook_data)
    
    # Then list webhooks
    response = client.get("/api/webhooks")
    assert response.status_code == 200
    webhooks = response.json()
    assert len(webhooks) == 1
    assert webhooks[0]["name"] == "Test Webhook"

def test_webhook_stats(client):
    """Test webhook statistics endpoint"""
    response = client.get("/api/stats")
    assert response.status_code == 200
    
    stats = response.json()
    assert "total" in stats
    assert "active" in stats
    assert "deliveries" in stats

def test_process_event(client):
    """Test event processing via API"""
    # Create webhook first
    webhook_data = {
        "name": "Test Event Handler",
        "url": "https://httpbin.org/post",
        "method": "POST",
        "auth_type": "none",
        "event_filters": [
            {"field": "level", "operator": "equals", "value": "error"}
        ]
    }
    
    client.post("/api/webhooks", json=webhook_data)
    
    # Send test event
    event_data = {
        "type": "error_event",
        "timestamp": "2025-05-20T10:30:00Z",
        "level": "error",
        "message": "Test error message",
        "source": "test_service",
        "metadata": {"test": True}
    }
    
    response = client.post("/api/events", json=event_data)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

def test_dashboard_endpoint(client):
    """Test dashboard HTML endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Webhook Integration Dashboard" in response.text

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
