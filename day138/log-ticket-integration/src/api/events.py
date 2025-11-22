"""Event processing API routes"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
import redis.asyncio as aioredis
import structlog

from src.models.log_event import LogEvent, EventBatch
from src.services.event_processor import EventProcessor
from src.utils.config import settings

logger = structlog.get_logger()
router = APIRouter()

# Redis connection for event queuing
redis_client = None


async def get_redis():
    global redis_client
    if not redis_client:
        redis_client = aioredis.from_url(settings.redis_url)
    return redis_client


async def get_event_processor() -> EventProcessor:
    from src.main import event_processor

    if not event_processor:
        raise HTTPException(status_code=503, detail="Event processor not available")
    return event_processor


@router.post("/submit")
async def submit_event(
    event: LogEvent,
    background_tasks: BackgroundTasks,
    redis: aioredis.Redis = Depends(get_redis),
) -> dict:
    """Submit a log event for processing"""

    try:
        # Queue event for processing
        await redis.rpush("events:pending", event.json())  # type: ignore

        logger.info(
            "Event queued for processing",
            event_id=event.id,
            service=event.service,
            level=event.level,
        )

        return {
            "message": "Event queued for processing",
            "event_id": event.id,
            "queue_position": await redis.llen("events:pending"),  # type: ignore
        }

    except Exception as e:
        logger.error("Failed to queue event", event_id=event.id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to queue event")


@router.post("/batch")
async def submit_event_batch(
    batch: EventBatch, redis: aioredis.Redis = Depends(get_redis)
) -> dict:
    """Submit multiple events in batch"""

    try:
        # Queue all events
        pipe = redis.pipeline()
        for event in batch.events:
            pipe.rpush("events:pending", event.json())
        await pipe.execute()

        logger.info(
            "Event batch queued", batch_id=batch.batch_id, event_count=len(batch.events)
        )

        return {
            "message": "Event batch queued successfully",
            "batch_id": batch.batch_id,
            "events_queued": len(batch.events),
            "total_queue_size": await redis.llen("events:pending"),  # type: ignore
        }

    except Exception as e:
        logger.error(
            "Failed to queue event batch", batch_id=batch.batch_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to queue event batch")


@router.get("/queue/status")
async def get_queue_status(redis: aioredis.Redis = Depends(get_redis)) -> dict:
    """Get event processing queue status"""

    try:
        pending_count = await redis.llen("events:pending")  # type: ignore
        processing_count = await redis.llen("events:processing")  # type: ignore

        return {
            "pending_events": pending_count,
            "processing_events": processing_count,
            "total_events": pending_count + processing_count,
        }

    except Exception as e:
        logger.error("Failed to get queue status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get queue status")


@router.post("/test/generate")
async def generate_test_events(
    count: int = 10, redis: aioredis.Redis = Depends(get_redis)
) -> dict:
    """Generate test events for demonstration"""

    import uuid
    from datetime import datetime, timedelta
    import random

    services = ["web-api", "payment-service", "user-auth", "database", "cache"]
    levels = ["info", "warning", "error", "critical"]
    components = ["handler", "processor", "connector", "validator"]

    error_templates = {
        "database": "Connection timeout to database server {host}",
        "api": "HTTP {status_code} error on endpoint {endpoint}",
        "auth": "Authentication failed for user {user_id}",
        "payment": "Payment processing failed: {error_code}",
        "cache": "Redis connection lost to {redis_host}",
    }

    events = []
    for i in range(count):
        service = random.choice(services)
        level = random.choice(levels)
        component = random.choice(components)

        # Weight towards more errors for demo
        if random.random() < 0.4:
            level = random.choice(["error", "critical"])

        # Generate realistic error message
        if service in error_templates:
            message = error_templates[service].format(
                host=f"db-{random.randint(1, 5)}.internal",
                status_code=random.choice([500, 502, 503, 504]),
                endpoint=f"/api/v1/{random.choice(['users', 'orders', 'payments'])}",
                user_id=f"user_{random.randint(1000, 9999)}",
                error_code=f"ERR_{random.randint(100, 999)}",
                redis_host=f"redis-{random.randint(1, 3)}.cache.internal",
            )
        else:
            message = f"Service {service} {level} in {component}"

        event = LogEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow() - timedelta(minutes=random.randint(0, 60)),
            level=level,
            service=service,
            component=component,
            message=message,
            host=f"host-{random.randint(1, 10)}.cluster.local",
            request_id=str(uuid.uuid4()),
            metadata={
                "environment": "production",
                "region": random.choice(["us-east-1", "us-west-2", "eu-west-1"]),
                "pod_id": f"pod-{random.randint(1, 20)}",
            },
        )

        # Queue event
        await redis.rpush("events:pending", event.json())  # type: ignore
        events.append(
            {
                "id": event.id,
                "service": event.service,
                "level": event.level,
                "message": (
                    event.message[:100] + "..."
                    if len(event.message) > 100
                    else event.message
                ),
            }
        )

    logger.info("Generated test events", count=count)

    return {
        "message": f"Generated {count} test events",
        "events": events,
        "queue_size": await redis.llen("events:pending"),  # type: ignore
    }
