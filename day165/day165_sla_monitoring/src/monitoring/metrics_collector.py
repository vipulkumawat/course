import asyncio
import random
import time
from datetime import datetime
from typing import List
import redis.asyncio as aioredis
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.models.sla_models import SLIMetric, MetricType, ServiceTier

class MetricsCollector:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.running = False
        
    async def start_collection(self):
        self.running = True
        print("📊 Metrics collection started")
        while self.running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(10)
            except Exception as e:
                print(f"Collection error: {e}")
                await asyncio.sleep(5)
    
    async def _collect_metrics(self):
        timestamp = datetime.now()
        for tier in ServiceTier:
            latency = self._gen_latency(tier)
            availability = self._gen_availability(tier)
            error_rate = self._gen_error_rate(tier)
            
            await self._store(SLIMetric(
                metric_type=MetricType.LATENCY,
                value=latency,
                timestamp=timestamp,
                service_tier=tier
            ))
            await self._store(SLIMetric(
                metric_type=MetricType.AVAILABILITY,
                value=availability,
                timestamp=timestamp,
                service_tier=tier
            ))
            await self._store(SLIMetric(
                metric_type=MetricType.ERROR_RATE,
                value=error_rate,
                timestamp=timestamp,
                service_tier=tier
            ))
    
    def _gen_latency(self, tier: ServiceTier) -> float:
        base = {ServiceTier.GOLD: 45, ServiceTier.SILVER: 95, ServiceTier.BRONZE: 180}[tier]
        if random.random() < 0.08:  # 8% spike chance
            return base * random.uniform(1.5, 2.5)
        return base + random.gauss(0, base * 0.1)
    
    def _gen_availability(self, tier: ServiceTier) -> float:
        base = {ServiceTier.GOLD: 99.98, ServiceTier.SILVER: 99.92, ServiceTier.BRONZE: 99.6}[tier]
        if random.random() < 0.03:
            return base - random.uniform(0.1, 0.5)
        return min(100, base + random.gauss(0, 0.02))
    
    def _gen_error_rate(self, tier: ServiceTier) -> float:
        base = {ServiceTier.GOLD: 0.005, ServiceTier.SILVER: 0.03, ServiceTier.BRONZE: 0.08}[tier]
        if random.random() < 0.05:
            return base * random.uniform(2, 5)
        return max(0, base + random.gauss(0, base * 0.3))
    
    async def _store(self, metric: SLIMetric):
        key = f"metrics:{metric.service_tier.value}:{metric.metric_type.value}"
        value = f"{metric.timestamp.isoformat()}|{metric.value}"
        await self.redis.lpush(key, value)
        await self.redis.ltrim(key, 0, 10000)
        await self.redis.expire(key, 604800)
    
    async def get_recent_metrics(self, tier: ServiceTier, metric_type: MetricType, window: int = 300) -> List[float]:
        key = f"metrics:{tier.value}:{metric_type.value}"
        values = await self.redis.lrange(key, 0, -1)
        cutoff = time.time() - window
        recent = []
        for v in values:
            ts, val = (v.decode() if isinstance(v, bytes) else v).split('|')
            if datetime.fromisoformat(ts).timestamp() >= cutoff:
                recent.append(float(val))
        return recent
    
    async def stop(self):
        self.running = False
