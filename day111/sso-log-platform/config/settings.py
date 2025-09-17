"""Configuration settings for SSO Log Platform"""
import os
from typing import Dict, Any

class Settings:
    """Application settings"""
    
    def __init__(self):
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID", "demo-client-id")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "demo-secret")
        self.okta_domain = os.getenv("OKTA_DOMAIN", "dev-test.okta.com")
        self.okta_client_id = os.getenv("OKTA_CLIENT_ID", "demo-client")
        self.okta_client_secret = os.getenv("OKTA_CLIENT_SECRET", "demo-secret")
        self.jwt_secret = os.getenv("JWT_SECRET", "development-secret")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for specific SSO provider"""
        if provider == "google":
            return {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo"
            }
        elif provider == "okta":
            return {
                "client_id": self.okta_client_id,
                "client_secret": self.okta_client_secret,
                "auth_url": f"https://{self.okta_domain}/oauth2/v1/authorize",
                "token_url": f"https://{self.okta_domain}/oauth2/v1/token",
                "userinfo_url": f"https://{self.okta_domain}/oauth2/v1/userinfo"
            }
        else:
            raise ValueError(f"Unsupported provider: {provider}")

settings = Settings()
