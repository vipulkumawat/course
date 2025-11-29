import pytest
from fastapi.testclient import TestClient
from src.main import app
from datetime import datetime, timedelta
import urllib3.exceptions

client = TestClient(app)

def get_auth_token():
    """Get authentication token for tests"""
    response = client.post(
        "/oauth/token",
        data={"username": "tableau", "password": "tableau_secret", "grant_type": "password"}
    )
    return response.json()["access_token"]

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_authentication():
    """Test OAuth authentication"""
    response = client.post(
        "/oauth/token",
        data={"username": "tableau", "password": "tableau_secret", "grant_type": "password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_schema_endpoint():
    """Test metrics schema endpoint"""
    token = get_auth_token()
    try:
        response = client.get(
            "/api/v1/metrics/schema",
            headers={"Authorization": f"Bearer {token}"}
        )
        # If InfluxDB is not available, the endpoint may return 500
        if response.status_code == 500:
            error_detail = response.json().get("detail", "")
            if "Connection refused" in str(error_detail) or "Failed to establish" in str(error_detail):
                pytest.skip("InfluxDB is not available - skipping integration test")
        
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "dimensions" in data
    except Exception as e:
        # Skip test if InfluxDB connection fails or any connection-related error occurs
        error_str = str(e)
        if any(keyword in error_str for keyword in ["Connection refused", "Failed to establish", "NewConnectionError", "ConnectionError"]):
            pytest.skip(f"InfluxDB is not available - skipping integration test: {e}")
        # Re-raise if it's a different error
        raise

def test_unauthorized_access():
    """Test unauthorized access is blocked"""
    response = client.get("/api/v1/metrics/schema")
    assert response.status_code == 401
