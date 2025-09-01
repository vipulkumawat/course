from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Mock authentication - replace with real JWT validation in production"""
    # For demo purposes, return a mock user
    return {
        "id": 1,
        "username": "demo_user",
        "email": "demo@example.com"
    }
