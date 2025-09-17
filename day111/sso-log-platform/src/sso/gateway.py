"""SSO Gateway - Central authentication entry point"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import base64
from urllib.parse import urlencode, parse_qs

from fastapi import FastAPI, Request, HTTPException, Depends, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
import redis
import jwt
from authlib.integrations.requests_client import OAuth2Session
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class SSOConfig:
    """SSO Configuration Management"""
    def __init__(self):
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID", "test-google-client-id")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "test-google-secret")
        self.okta_domain = os.getenv("OKTA_DOMAIN", "dev-test.okta.com")
        self.okta_client_id = os.getenv("OKTA_CLIENT_ID", "test-okta-client")
        self.okta_client_secret = os.getenv("OKTA_CLIENT_SECRET", "test-okta-secret")
        self.jwt_secret = os.getenv("JWT_SECRET", "test-jwt-secret-key-for-development")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.environment = os.getenv("ENVIRONMENT", "development")
        
class AuthToken(BaseModel):
    """JWT Authentication Token Model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: Dict[str, Any]

class SSOGateway:
    """Main SSO Gateway Implementation"""
    
    def __init__(self):
        self.config = SSOConfig()
        self.redis_client = redis.from_url(self.config.redis_url, decode_responses=True)
        self.templates = Jinja2Templates(directory="templates")
        
    def generate_jwt_token(self, user_info: Dict[str, Any], tenant_id: str) -> str:
        """Generate JWT token for authenticated user"""
        payload = {
            "sub": user_info.get("id") or user_info.get("email"),
            "email": user_info["email"],
            "name": user_info.get("name", ""),
            "tenant_id": tenant_id,
            "provider": user_info.get("provider", "unknown"),
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24),
            "aud": "log-platform",
            "iss": "sso-gateway"
        }
        return jwt.encode(payload, self.config.jwt_secret, algorithm="HS256")
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=["HS256"], audience="log-platform")
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_google_auth_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL"""
        params = {
            "client_id": self.config.google_client_id,
            "redirect_uri": f"{self.config.base_url}/auth/google/callback",
            "scope": "openid email profile",
            "response_type": "code",
            "state": state
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    def get_okta_auth_url(self, state: str) -> str:
        """Generate Okta OAuth authorization URL"""
        params = {
            "client_id": self.config.okta_client_id,
            "redirect_uri": f"{self.config.base_url}/auth/okta/callback",
            "scope": "openid email profile",
            "response_type": "code",
            "state": state
        }
        return f"https://{self.config.okta_domain}/oauth2/v1/authorize?{urlencode(params)}"
    
    async def exchange_google_code(self, code: str) -> Dict[str, Any]:
        """Exchange Google authorization code for user info"""
        import httpx
        
        # Exchange code for token
        token_data = {
            "client_id": self.config.google_client_id,
            "client_secret": self.config.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{self.config.base_url}/auth/google/callback"
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post("https://oauth2.googleapis.com/token", data=token_data)
            token_info = token_response.json()
            
            if "access_token" not in token_info:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            # Get user info
            headers = {"Authorization": f"Bearer {token_info['access_token']}"}
            user_response = await client.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=headers)
            user_info = user_response.json()
            user_info["provider"] = "google"
            
            return user_info
    
    async def exchange_okta_code(self, code: str) -> Dict[str, Any]:
        """Exchange Okta authorization code for user info"""
        import httpx
        
        # Exchange code for token
        token_data = {
            "client_id": self.config.okta_client_id,
            "client_secret": self.config.okta_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{self.config.base_url}/auth/okta/callback"
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(f"https://{self.config.okta_domain}/oauth2/v1/token", data=token_data)
            token_info = token_response.json()
            
            if "access_token" not in token_info:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            # Get user info
            headers = {"Authorization": f"Bearer {token_info['access_token']}"}
            user_response = await client.get(f"https://{self.config.okta_domain}/oauth2/v1/userinfo", headers=headers)
            user_info = user_response.json()
            user_info["provider"] = "okta"
            
            return user_info
    
    def determine_tenant_from_email(self, email: str) -> str:
        """Determine tenant ID from email domain"""
        domain = email.split("@")[1]
        # Simple tenant mapping - in production, this would be configurable
        tenant_mapping = {
            "gmail.com": "demo-tenant",
            "google.com": "google-corp",
            "test.com": "test-tenant"
        }
        return tenant_mapping.get(domain, "default-tenant")
    
    def store_session(self, session_id: str, user_data: Dict[str, Any]) -> None:
        """Store user session in Redis"""
        session_data = {
            "user_info": json.dumps(user_data),
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat()
        }
        self.redis_client.hset(f"session:{session_id}", mapping=session_data)
        self.redis_client.expire(f"session:{session_id}", 86400)  # 24 hours
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user session from Redis"""
        session_data = self.redis_client.hgetall(f"session:{session_id}")
        if session_data:
            return {
                "user_info": json.loads(session_data["user_info"]),
                "created_at": session_data["created_at"],
                "last_accessed": session_data["last_accessed"]
            }
        return None

# Global SSO gateway instance
sso_gateway = SSOGateway()
