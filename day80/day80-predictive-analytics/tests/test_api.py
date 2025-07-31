import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app

client = TestClient(app)

class TestAPI:
    
    def test_root_endpoint(self):
        """Test API root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
    
    def test_predictions_endpoint(self):
        """Test predictions endpoint"""
        response = client.get("/predictions")
        assert response.status_code == 200
        data = response.json()
        assert "ensemble_prediction" in data
        assert "ensemble_confidence" in data
        assert "timestamps" in data
    
    def test_forecast_endpoint(self):
        """Test forecast endpoint with custom steps"""
        response = client.get("/forecast/6")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ensemble_prediction"]) == 6
        assert len(data["timestamps"]) == 6
    
    def test_forecast_invalid_steps(self):
        """Test forecast endpoint with invalid steps"""
        response = client.get("/forecast/0")
        assert response.status_code == 400
        
        response = client.get("/forecast/500")
        assert response.status_code == 400
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "models_active" in data
        assert "forecast_confidence" in data
