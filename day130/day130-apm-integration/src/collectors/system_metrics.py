import asyncio
import psutil
import time
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime
import structlog
import redis.asyncio as redis

logger = structlog.get_logger()

@dataclass
class SystemMetrics:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_io: Dict[str, Any]
    network_io: Dict[str, Any]
    load_average: tuple

class SystemMetricsCollector:
    def __init__(self, redis_client: redis.Redis, collection_interval: int = 5):
        self.redis_client = redis_client
        self.collection_interval = collection_interval
        self.running = False
        
    async def start_collection(self):
        """Start collecting system metrics"""
        self.running = True
        logger.info("Starting system metrics collection")
        
        while self.running:
            try:
                metrics = await self._collect_metrics()
                await self._store_metrics(metrics)
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error("Error collecting metrics", error=str(e))
                
    async def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        disk_io = psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
        net_io = psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
        
        return SystemMetrics(
            timestamp=time.time(),
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=psutil.virtual_memory().percent,
            disk_io=disk_io,
            network_io=net_io,
            load_average=psutil.getloadavg()
        )
    
    async def _store_metrics(self, metrics: SystemMetrics):
        """Store metrics in Redis time series"""
        key = f"metrics:{int(metrics.timestamp)}"
        data = {
            "timestamp": metrics.timestamp,
            "cpu": metrics.cpu_percent,
            "memory": metrics.memory_percent,
            "load_1": metrics.load_average[0],
            "load_5": metrics.load_average[1], 
            "load_15": metrics.load_average[2]
        }
        
        await self.redis_client.hset(key, mapping=data)
        await self.redis_client.expire(key, 86400)  # 24 hours retention
        
    def stop(self):
        """Stop metrics collection"""
        self.running = False
        logger.info("Stopped system metrics collection")
