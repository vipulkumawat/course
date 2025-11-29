import redis
import json
import hashlib
from typing import Optional
from src.models import BIDataResponse, MetricQuery
from config.settings import settings

class CacheLayer:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    def generate_cache_key(self, query: MetricQuery, user_services: list) -> str:
        """Generate unique cache key from query and user context"""
        query_dict = query.model_dump()
        query_dict['user_services'] = sorted(user_services)
        query_str = json.dumps(query_dict, sort_keys=True, default=str)
        return f"bi_query:{hashlib.sha256(query_str.encode()).hexdigest()}"
    
    def get(self, cache_key: str) -> Optional[BIDataResponse]:
        """Get cached query result"""
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            data_dict = json.loads(cached_data)
            return BIDataResponse(**data_dict)
        return None
    
    def set(self, cache_key: str, response: BIDataResponse, ttl: int = None):
        """Cache query result"""
        if ttl is None:
            ttl = settings.CACHE_TTL
        self.redis_client.setex(
            cache_key,
            ttl,
            response.model_dump_json()
        )
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all cache keys matching pattern"""
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
