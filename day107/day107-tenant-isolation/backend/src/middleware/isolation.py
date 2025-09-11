"""Tenant isolation middleware."""
import os
import asyncio
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.quota_engine import QuotaEngine, QuotaViolationError
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

class TenantIsolationMiddleware:
    """Middleware for tenant isolation and quota enforcement."""
    
    def __init__(self, quota_engine: QuotaEngine):
        self.quota_engine = quota_engine
    
    async def __call__(self, request: Request, call_next):
        """Process request with tenant isolation."""
        # Skip quota checks for WebSocket connections
        if request.url.path.startswith("/ws/"):
            return await call_next(request)
        
        # Extract tenant ID from headers or token
        tenant_id = request.headers.get("X-Tenant-ID", "default")
        
        # Set tenant context in request
        request.state.tenant_id = tenant_id
        request.state.tenant_path = self.quota_engine.get_tenant_path(tenant_id)
        
        try:
            # Check quota before processing
            await self._check_quota(tenant_id, request)
            
            # Process request
            response = await call_next(request)
            
            return response
        
        except QuotaViolationError as e:
            raise HTTPException(status_code=429, detail=f"Quota exceeded: {str(e)}")
        except Exception as e:
            logger.error(f"Error in isolation middleware: {e}")
            raise
    
    async def _check_quota(self, tenant_id: str, request: Request):
        """Check resource quotas for request."""
        try:
            # Check if quota is defined for this tenant
            if tenant_id not in self.quota_engine.quotas:
                logger.warning(f"No quota defined for tenant {tenant_id}, allowing request")
                return
            
            # Check rate limiting
            if not await self.quota_engine.check_quota(tenant_id, "requests"):
                raise QuotaViolationError("Rate limit exceeded")
            
            # Check connection quota
            if not await self.quota_engine.check_quota(tenant_id, "connections"):
                raise QuotaViolationError("Connection limit exceeded")
            
            # Allocate resources for this request
            await self.quota_engine.allocate_resources(tenant_id, cpu=0.1, memory=10, connections=1)
            
        except ValueError as e:
            # No quota defined - allow but log
            logger.warning(f"No quota defined for tenant {tenant_id}: {e}")
        except Exception as e:
            # Log error but don't block request
            logger.error(f"Error checking quota for tenant {tenant_id}: {e}")

def get_tenant_context(request: Request) -> tuple[str, str]:
    """Extract tenant context from request."""
    tenant_id = getattr(request.state, 'tenant_id', 'default')
    tenant_path = getattr(request.state, 'tenant_path', 'data/tenant_data/default')
    return tenant_id, tenant_path

async def verify_tenant_access(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify tenant has access to requested resources."""
    # Simplified auth - in production, verify JWT token
    token = credentials.credentials
    if not token or len(token) < 10:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Extract tenant ID from token (simplified)
    tenant_id = token.split('-')[0] if '-' in token else 'default'
    return tenant_id
