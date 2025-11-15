import asyncio
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog
import redis.asyncio as redis

logger = structlog.get_logger()

@dataclass  
class AppMetrics:
    timestamp: float
    request_count: int
    error_count: int
    response_time_avg: float
    response_time_p95: float
    active_connections: int

class AppMetricsCollector:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.active_connections = 0
        
    async def record_request(self, response_time: float, is_error: bool = False):
        """Record a request with response time"""
        self.request_count += 1
        if is_error:
            self.error_count += 1
        self.response_times.append(response_time)
        
        # Keep only last 100 response times for memory efficiency
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]
    
    async def get_current_metrics(self) -> AppMetrics:
        """Get current application metrics"""
        response_times = self.response_times.copy()
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate P95
        if response_times:
            sorted_times = sorted(response_times)
            p95_index = int(0.95 * len(sorted_times))
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
        else:
            p95_response_time = 0
            
        return AppMetrics(
            timestamp=time.time(),
            request_count=self.request_count,
            error_count=self.error_count,
            response_time_avg=avg_response_time,
            response_time_p95=p95_response_time,
            active_connections=self.active_connections
        )
    
    async def store_metrics(self):
        """Store current metrics snapshot"""
        metrics = await self.get_current_metrics()
        key = f"app_metrics:{int(metrics.timestamp)}"
        
        data = {
            "timestamp": metrics.timestamp,
            "requests": metrics.request_count,
            "errors": metrics.error_count,
            "avg_response": metrics.response_time_avg,
            "p95_response": metrics.response_time_p95,
            "connections": metrics.active_connections
        }
        
        await self.redis_client.hset(key, mapping=data)
        await self.redis_client.expire(key, 86400)
        
        # Reset counters after storing
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
