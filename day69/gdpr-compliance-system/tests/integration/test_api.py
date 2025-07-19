import pytest
from fastapi.testclient import TestClient
from src.backend.api.main import app

client = TestClient(app)

def test_create_erasure_request():
    """Test creating an erasure request via API"""
    response = client.post("/api/erasure-requests", json={
        "user_id": "test_user_123",
        "request_type": "DELETE"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user_123"
    assert data["status"] == "PENDING"
    assert "request_id" in data

def test_track_user_data():
    """Test tracking user data via API"""
    response = client.post("/api/user-data-tracking", json={
        "user_id": "test_user_123",
        "data_type": "user_logs",
        "storage_location": "postgresql_main",
        "data_path": "/logs/user_activity"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "mapping_id" in data
    assert data["message"] == "User data tracked successfully"

def test_get_statistics():
    """Test getting system statistics"""
    response = client.get("/api/statistics")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_mappings" in data
    assert "unique_users" in data
    assert "total_erasure_requests" in data
