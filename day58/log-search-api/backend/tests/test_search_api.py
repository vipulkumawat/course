import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_search_endpoint_without_auth():
    response = client.get("/api/v1/logs/search?q=test")
    assert response.status_code == 401

def test_auth_endpoint():
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "secret"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_search_with_auth():
    # Get token first
    auth_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "secret"}
    )
    token = auth_response.json()["access_token"]
    
    # Use token for search
    response = client.get(
        "/api/v1/logs/search?q=test",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "results" in response.json()
