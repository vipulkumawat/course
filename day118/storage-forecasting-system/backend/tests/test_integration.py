import pytest
import asyncio
import json
from httpx import AsyncClient
import sys
import os

# Add src to path  
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.api.forecast_api import app

class TestAPIIntegration:
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            
    @pytest.mark.asyncio
    async def test_current_metrics_endpoint(self):
        """Test current metrics endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/api/metrics/current")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "data" in data
            assert "used_gb" in data["data"]
            
    @pytest.mark.asyncio
    async def test_historical_metrics_endpoint(self):
        """Test historical metrics endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/api/metrics/historical?days=7")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "data" in data
            assert len(data["data"]) > 0
            
    @pytest.mark.asyncio
    async def test_forecast_generation(self):
        """Test forecast generation endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/api/forecast/generate", 
                                   json={"horizon_days": 7})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "forecast" in data
            assert "cost_analysis" in data
            assert "recommendation" in data
            
    @pytest.mark.asyncio
    async def test_dashboard_summary(self):
        """Test dashboard summary endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/api/dashboard/summary")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "data" in data
            summary = data["data"]
            assert "current_usage_gb" in summary
            assert "predicted_usage_30d_gb" in summary
            assert "growth_rate_percent" in summary

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
