import time
import redis
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str = "redis://localhost:6379", 
                 default_limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.redis = redis.from_url(redis_url)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.startswith("/api/v1/health"):
            return await call_next(request)
        
        # Get client identifier
        client_id = self.get_client_id(request)
        
        # Check rate limit
        if not self.is_allowed(client_id):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.default_limit} requests per {self.window_seconds} seconds"
                }
            )
        
        response = await call_next(request)
        return response
    
    def get_client_id(self, request: Request) -> str:
        # Use API key or IP address
        api_key = request.headers.get("Authorization")
        if api_key:
            return f"api_key:{api_key}"
        
        client_ip = request.client.host
        return f"ip:{client_ip}"
    
    def is_allowed(self, client_id: str) -> bool:
        current_time = int(time.time())
        window_start = current_time - self.window_seconds
        
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(client_id, 0, window_start)
        pipe.zcard(client_id)
        pipe.zadd(client_id, {str(current_time): current_time})
        pipe.expire(client_id, self.window_seconds)
        
        results = pipe.execute()
        request_count = results[1]
        
        return request_count < self.default_limit
