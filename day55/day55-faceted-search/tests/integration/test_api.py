import pytest
import requests
import time

BASE_URL = "http://localhost:8000/api"

def test_health_check():
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_generate_logs():
    response = requests.post(f"{BASE_URL}/logs/generate?count=10")
    assert response.status_code == 200
    data = response.json()
    assert "Generated 10 logs" in data["message"]

def test_search_api():
    # First generate some logs
    requests.post(f"{BASE_URL}/logs/generate?count=50")
    time.sleep(2)  # Wait for indexing
    
    # Test search
    search_request = {
        "query": "",
        "filters": {},
        "limit": 10
    }
    
    response = requests.post(f"{BASE_URL}/search/", json=search_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "logs" in data
    assert "facets" in data
    assert "total_count" in data
    assert data["total_count"] >= 0

def test_facets_api():
    response = requests.get(f"{BASE_URL}/search/facets")
    assert response.status_code == 200
    
    data = response.json()
    assert "facets" in data
    assert "total_logs" in data

def test_search_with_filters():
    # Generate logs first
    requests.post(f"{BASE_URL}/logs/generate?count=30")
    time.sleep(2)
    
    # Search with service filter
    search_request = {
        "query": "",
        "filters": {"service": ["user-api"]},
        "limit": 20
    }
    
    response = requests.post(f"{BASE_URL}/search/", json=search_request)
    assert response.status_code == 200
    
    data = response.json()
    # All returned logs should be from user-api service
    for log in data["logs"]:
        assert log["service"] == "user-api"

if __name__ == "__main__":
    pytest.main([__file__])
