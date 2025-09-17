"""Unit tests for SSO Gateway"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from sso.gateway import SSOGateway, SSOConfig

class TestSSOGateway:
    @pytest.fixture
    def sso_gateway(self):
        with patch('redis.from_url'):
            gateway = SSOGateway()
            gateway.redis_client = Mock()
            return gateway
    
    def test_generate_jwt_token(self, sso_gateway):
        """Test JWT token generation"""
        user_info = {
            "id": "123",
            "email": "test@example.com",
            "name": "Test User"
        }
        tenant_id = "test-tenant"
        
        token = sso_gateway.generate_jwt_token(user_info, tenant_id)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Validate token
        payload = sso_gateway.validate_jwt_token(token)
        assert payload is not None
        assert payload["email"] == "test@example.com"
        assert payload["tenant_id"] == "test-tenant"
    
    def test_validate_jwt_token_expired(self, sso_gateway):
        """Test JWT token validation with expired token"""
        # Create token with past expiration
        user_info = {"email": "test@example.com"}
        
        with patch('sso.gateway.datetime') as mock_datetime:
            # Set datetime to past for token generation
            mock_datetime.utcnow.return_value = datetime.utcnow() - timedelta(hours=25)
            token = sso_gateway.generate_jwt_token(user_info, "test-tenant")
        
        # Should return None for expired token
        payload = sso_gateway.validate_jwt_token(token)
        assert payload is None
    
    def test_determine_tenant_from_email(self, sso_gateway):
        """Test tenant determination from email"""
        tenant = sso_gateway.determine_tenant_from_email("user@gmail.com")
        assert tenant == "demo-tenant"
        
        tenant = sso_gateway.determine_tenant_from_email("user@unknown.com")
        assert tenant == "default-tenant"
    
    def test_get_google_auth_url(self, sso_gateway):
        """Test Google OAuth URL generation"""
        state = "test-state"
        url = sso_gateway.get_google_auth_url(state)
        
        assert "accounts.google.com" in url
        assert f"state={state}" in url
        assert "scope=openid+email+profile" in url
    
    def test_get_okta_auth_url(self, sso_gateway):
        """Test Okta OAuth URL generation"""
        state = "test-state"
        url = sso_gateway.get_okta_auth_url(state)
        
        assert sso_gateway.config.okta_domain in url
        assert f"state={state}" in url
        assert "scope=openid+email+profile" in url
    
    @pytest.mark.asyncio
    async def test_exchange_google_code_success(self, sso_gateway):
        """Test successful Google code exchange"""
        mock_token_response = Mock()
        mock_token_response.json.return_value = {"access_token": "test-token"}
        
        mock_user_response = Mock()
        mock_user_response.json.return_value = {
            "id": "123",
            "email": "test@gmail.com",
            "name": "Test User"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = mock_client.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_token_response)
            mock_client_instance.get = AsyncMock(return_value=mock_user_response)
            
            user_info = await sso_gateway.exchange_google_code("test-code")
            
            assert user_info["email"] == "test@gmail.com"
            assert user_info["provider"] == "google"
