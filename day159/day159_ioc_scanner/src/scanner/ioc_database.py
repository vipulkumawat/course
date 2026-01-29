import redis
import json
import hashlib
from typing import List, Optional, Set
from datetime import datetime, timedelta
from bloom_filter2 import BloomFilter
from .models import IOCIndicator, IOCType, Severity
import structlog

logger = structlog.get_logger()

class IOCDatabase:
    """Manages IOC storage and retrieval using Redis and Bloom filters"""
    
    def __init__(self, redis_client: redis.Redis, cache_ttl: int = 3600):
        self.redis = redis_client
        self.cache_ttl = cache_ttl
        
        # Initialize Bloom filters for fast negative lookups
        self.ip_bloom = BloomFilter(max_elements=1000000, error_rate=0.001)
        self.domain_bloom = BloomFilter(max_elements=500000, error_rate=0.001)
        self.hash_bloom = BloomFilter(max_elements=500000, error_rate=0.001)
        
        self.stats = {
            "total_iocs": 0,
            "lookups": 0,
            "hits": 0,
            "cache_hits": 0
        }
        
        logger.info("IOC database initialized")
    
    def add_ioc(self, ioc: IOCIndicator) -> bool:
        """Add IOC to database"""
        try:
            key = f"ioc:{ioc.ioc_type.value}:{ioc.value}"
            
            # Store in Redis with TTL
            self.redis.setex(
                key,
                self.cache_ttl,
                json.dumps(ioc.to_dict())
            )
            
            # Add to appropriate Bloom filter
            if ioc.ioc_type == IOCType.IP_ADDRESS:
                self.ip_bloom.add(ioc.value)
            elif ioc.ioc_type == IOCType.DOMAIN:
                self.domain_bloom.add(ioc.value)
            elif ioc.ioc_type == IOCType.FILE_HASH:
                self.hash_bloom.add(ioc.value)
            
            # Add to type index
            self.redis.sadd(f"ioc_index:{ioc.ioc_type.value}", ioc.value)
            
            self.stats["total_iocs"] += 1
            return True
            
        except Exception as e:
            logger.error("Failed to add IOC", error=str(e), ioc=ioc.value)
            return False
    
    def lookup_ioc(self, value: str, ioc_type: IOCType) -> Optional[IOCIndicator]:
        """Lookup IOC in database"""
        self.stats["lookups"] += 1
        
        # Fast negative lookup using Bloom filter
        if ioc_type == IOCType.IP_ADDRESS and value not in self.ip_bloom:
            return None
        elif ioc_type == IOCType.DOMAIN and value not in self.domain_bloom:
            return None
        elif ioc_type == IOCType.FILE_HASH and value not in self.hash_bloom:
            return None
        
        # Check Redis cache
        key = f"ioc:{ioc_type.value}:{value}"
        cached = self.redis.get(key)
        
        if cached:
            self.stats["cache_hits"] += 1
            self.stats["hits"] += 1
            data = json.loads(cached)
            return IOCIndicator(
                value=data["value"],
                ioc_type=IOCType(data["type"]),
                severity=Severity(data["severity"]),
                source=data["source"],
                description=data.get("description", ""),
                confidence=data.get("confidence", 1.0),
                metadata=data.get("metadata", {})
            )
        
        return None
    
    def batch_lookup(self, values: List[tuple]) -> List[IOCIndicator]:
        """Batch lookup multiple IOCs"""
        results = []
        for value, ioc_type in values:
            match = self.lookup_ioc(value, ioc_type)
            if match:
                results.append(match)
        return results
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        return {
            **self.stats,
            "cache_hit_rate": (self.stats["cache_hits"] / self.stats["lookups"] * 100) 
                              if self.stats["lookups"] > 0 else 0,
            "hit_rate": (self.stats["hits"] / self.stats["lookups"] * 100) 
                        if self.stats["lookups"] > 0 else 0
        }
