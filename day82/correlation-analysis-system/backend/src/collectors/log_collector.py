import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import structlog

logger = structlog.get_logger()

@dataclass
class LogEvent:
    timestamp: datetime
    source: str
    service: str
    level: str
    message: str
    user_id: str = None
    session_id: str = None
    correlation_id: str = None
    metrics: Dict[str, Any] = None

class LogCollector:
    def __init__(self):
        self.event_queue = asyncio.Queue()
        self.sources = ["web", "database", "api", "payment", "inventory"]
        self.running = False
        
    async def start_collection(self):
        """Start collecting logs from different sources"""
        self.running = True
        logger.info("Starting log collection from multiple sources")
        
        # Start collectors for each source
        tasks = []
        for source in self.sources:
            task = asyncio.create_task(self._collect_from_source(source))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def _collect_from_source(self, source: str):
        """Simulate log collection from a specific source"""
        while self.running:
            log_event = self._generate_log_event(source)
            await self.event_queue.put(log_event)
            
            # Vary collection frequency by source
            delay = random.uniform(0.1, 2.0)
            await asyncio.sleep(delay)
    
    def _generate_log_event(self, source: str) -> LogEvent:
        """Generate realistic log events"""
        user_id = f"user_{random.randint(1, 1000)}"
        session_id = f"session_{random.randint(1, 100)}"
        correlation_id = f"corr_{random.randint(1, 50)}"
        
        # Create correlated events based on scenarios
        if source == "web":
            return LogEvent(
                timestamp=datetime.now(),
                source=source,
                service="nginx",
                level=random.choice(["INFO", "WARN", "ERROR"]),
                message=f"HTTP {random.choice([200, 404, 500])} - {random.choice(['GET', 'POST'])} /api/checkout",
                user_id=user_id,
                session_id=session_id,
                correlation_id=correlation_id,
                metrics={"response_time": random.uniform(50, 500), "status_code": random.choice([200, 404, 500])}
            )
        elif source == "database":
            return LogEvent(
                timestamp=datetime.now(),
                source=source,
                service="postgresql",
                level=random.choice(["INFO", "WARN", "ERROR"]),
                message=f"Query execution - {random.choice(['SELECT', 'INSERT', 'UPDATE'])}",
                user_id=user_id,
                correlation_id=correlation_id,
                metrics={"query_time": random.uniform(10, 200), "connections": random.randint(10, 100)}
            )
        elif source == "api":
            return LogEvent(
                timestamp=datetime.now(),
                source=source,
                service="checkout-api",
                level=random.choice(["INFO", "WARN", "ERROR"]),
                message=f"API call - {random.choice(['process_payment', 'validate_cart', 'update_inventory'])}",
                user_id=user_id,
                session_id=session_id,
                correlation_id=correlation_id,
                metrics={"latency": random.uniform(20, 300), "memory_usage": random.uniform(30, 90)}
            )
        elif source == "payment":
            return LogEvent(
                timestamp=datetime.now(),
                source=source,
                service="payment-processor",
                level=random.choice(["INFO", "WARN", "ERROR"]),
                message=f"Payment {random.choice(['authorized', 'declined', 'pending'])}",
                user_id=user_id,
                correlation_id=correlation_id,
                metrics={"amount": random.uniform(10, 500), "processing_time": random.uniform(100, 1000)}
            )
        else:  # inventory
            return LogEvent(
                timestamp=datetime.now(),
                source=source,
                service="inventory-service",
                level=random.choice(["INFO", "WARN", "ERROR"]),
                message=f"Stock {random.choice(['updated', 'depleted', 'reserved'])}",
                correlation_id=correlation_id,
                metrics={"stock_level": random.randint(0, 100), "update_time": random.uniform(5, 50)}
            )
    
    async def get_events(self, count: int = 100) -> List[LogEvent]:
        """Get recent events for correlation analysis"""
        events = []
        temp_queue = asyncio.Queue()
        
        # Get events from queue without blocking
        for _ in range(min(count, self.event_queue.qsize())):
            try:
                event = self.event_queue.get_nowait()
                events.append(event)
                await temp_queue.put(event)  # Put back for processing
            except asyncio.QueueEmpty:
                break
        
        # Put events back
        while not temp_queue.empty():
            event = await temp_queue.get()
            await self.event_queue.put(event)
        
        return events
    
    def stop_collection(self):
        """Stop log collection"""
        self.running = False
        logger.info("Stopped log collection")
