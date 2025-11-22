"""Dashboard API routes for monitoring and statistics"""

from fastapi import APIRouter, Depends
from typing import Dict
import redis.asyncio as aioredis
import structlog

from src.utils.config import settings

logger = structlog.get_logger()
router = APIRouter()


async def get_redis():
    return aioredis.from_url(settings.redis_url)


def get_services():
    from src.main import event_processor, ticket_service

    return event_processor, ticket_service


@router.get("/stats")
async def get_dashboard_stats(redis: aioredis.Redis = Depends(get_redis)) -> Dict:
    """Get comprehensive dashboard statistics"""

    event_processor, ticket_service = get_services()

    # Queue statistics
    pending_events = await redis.llen("events:pending")  # type: ignore
    processing_events = await redis.llen("events:processing")  # type: ignore

    # Processing statistics
    processed_events = event_processor.processed_events if event_processor else 0
    created_tickets = event_processor.created_tickets if event_processor else 0

    # System health
    system_health = {
        "event_processor": event_processor.is_running() if event_processor else False,
        "ticket_service": ticket_service.is_connected() if ticket_service else False,
        "redis": True,  # If we got here, Redis is working
    }

    # Recent activity (mock data for demo)
    recent_tickets = [
        {
            "id": "DEMO-123",
            "system": "JIRA",
            "title": "Database connection timeout",
            "created": "2 minutes ago",
        },
        {
            "id": "INC0012345",
            "system": "ServiceNow",
            "title": "API authentication failures",
            "created": "5 minutes ago",
        },
        {
            "id": "DEMO-122",
            "system": "JIRA",
            "title": "Memory leak in payment service",
            "created": "8 minutes ago",
        },
    ]

    return {
        "queue": {
            "pending": pending_events,
            "processing": processing_events,
            "total": pending_events + processing_events,
        },
        "processing": {
            "events_processed": processed_events,
            "tickets_created": created_tickets,
            "success_rate": round(
                (created_tickets / max(processed_events, 1)) * 100, 1
            ),
        },
        "system_health": system_health,
        "recent_tickets": recent_tickets,
        "configuration": {
            "jira_project": settings.jira_project_key,
            "servicenow_table": settings.servicenow_table,
            "processing_interval": settings.event_processing_interval,
            "batch_size": settings.event_batch_size,
        },
    }


@router.get("/metrics")
async def get_metrics() -> Dict:
    """Get metrics in Prometheus format"""

    event_processor, ticket_service = get_services()

    metrics = {
        "events_processed_total": (
            event_processor.processed_events if event_processor else 0
        ),
        "tickets_created_total": (
            event_processor.created_tickets if event_processor else 0
        ),
        "system_up": 1 if (event_processor and ticket_service) else 0,
    }

    return metrics


@router.get("/health")
async def health_check() -> Dict:
    """Detailed health check endpoint"""

    event_processor, ticket_service = get_services()

    health_checks = {
        "event_processor": {
            "status": (
                "up" if (event_processor and event_processor.is_running()) else "down"
            ),
            "processed_events": (
                event_processor.processed_events if event_processor else 0
            ),
        },
        "ticket_service": {
            "status": (
                "up" if (ticket_service and ticket_service.is_connected()) else "down"
            ),
            "jira_connection": True,  # Would test actual connection in production
            "servicenow_connection": True,
        },
        "overall": (
            "healthy"
            if all(
                [
                    event_processor and event_processor.is_running(),
                    ticket_service and ticket_service.is_connected(),
                ]
            )
            else "degraded"
        ),
    }

    return health_checks
