"""Integration tests for authentication flows"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.main import app

class TestAuthFlow:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_login_page_loads(self, client):
        """Test login page loads correctly"""
        response = client.get("/login")
        assert response.status_code == 200
        assert "Continue with Google" in response.text
        assert "Continue with Okta" in response.text
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_unauthenticated_redirect(self, client):
        """Test unauthenticated users are redirected to login"""
        response = client.get("/", allow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["location"]
    
    def test_api_user_unauthenticated(self, client):
        """Test API user endpoint without authentication"""
        response = client.get("/api/user")
        assert response.status_code == 401
    
    def test_initiate_google_auth(self, client):
        """Test initiating Google authentication"""
        with patch('sso.gateway.sso_gateway.redis_client') as mock_redis:
            mock_redis.setex = AsyncMock()
            response = client.get("/auth/google", allow_redirects=False)
            assert response.status_code == 302
            assert "accounts.google.com" in response.headers["location"]
    
    def test_initiate_okta_auth(self, client):
        """Test initiating Okta authentication"""
        with patch('sso.gateway.sso_gateway.redis_client') as mock_redis:
            mock_redis.setex = AsyncMock()
            response = client.get("/auth/okta", allow_redirects=False)
            assert response.status_code == 302
            location = response.headers["location"]
            assert "okta.com" in location
    
    def test_invalid_provider(self, client):
        """Test authentication with invalid provider"""
        response = client.get("/auth/invalid-provider")
        assert response.status_code == 400
