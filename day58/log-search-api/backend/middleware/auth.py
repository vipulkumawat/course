from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from services.auth_service import get_current_user

security = HTTPBearer()

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        public_paths = ["/api/docs", "/api/redoc", "/api/v1/auth/", "/api/v1/health"]
        
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        response = await call_next(request)
        return response

async def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = await get_current_user(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user
