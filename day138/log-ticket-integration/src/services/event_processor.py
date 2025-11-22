"""Event processing service for log analysis and ticket creation"""

import asyncio
import hashlib
import json
from typing import List, Optional
import structlog
import redis.asyncio as aioredis

from src.models.log_event import LogEvent
from src.models.ticket import TicketRequest
from src.services.ticket_service import TicketService
from src.utils.config import settings

logger = structlog.get_logger()


class EventProcessor:
    """Processes log events and creates tickets"""

    def __init__(self, ticket_service: TicketService):
        self.ticket_service = ticket_service
        self.redis = None
        self.running = False
        self._task = None
        self.processed_events = 0
        self.created_tickets = 0

    async def start(self):
        """Start the event processor"""
        self.redis = aioredis.from_url(settings.redis_url)
        self.running = True
        self._task = asyncio.create_task(self._process_events_loop())
        logger.info("Event processor started")

    async def stop(self):
        """Stop the event processor"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.redis:
            await self.redis.close()
        logger.info("Event processor stopped")

    def is_running(self) -> bool:
        """Check if processor is running"""
        return self.running

    async def process_event(self, event: LogEvent) -> Optional[str]:
        """Process a single log event"""
        try:
            # Classify event
            classification = await self._classify_event(event)

            if not classification.should_create_ticket:
                return None

            # Generate incident fingerprint for deduplication
            fingerprint = self._generate_fingerprint(event)

            # Check for existing ticket
            existing_ticket = await self._check_existing_ticket(fingerprint)
            if existing_ticket:
                await self._update_existing_ticket(existing_ticket, event)
                return existing_ticket

            # Create new ticket
            ticket_request = await self._create_ticket_request(event, classification)
            ticket_id = await self.ticket_service.create_ticket(ticket_request)

            if ticket_id:
                await self._store_ticket_fingerprint(fingerprint, ticket_id)
                self.created_tickets += 1
                logger.info("Created ticket", ticket_id=ticket_id, event_id=event.id)

            return ticket_id

        except Exception as e:
            logger.error("Error processing event", event_id=event.id, error=str(e))
            return None

    async def _process_events_loop(self):
        """Main event processing loop"""
        while self.running:
            try:
                # Get events from Redis queue
                events = await self._get_pending_events()

                if events:
                    tasks = [self.process_event(event) for event in events]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    successful = sum(
                        1 for r in results if r and not isinstance(r, Exception)
                    )
                    self.processed_events += len(events)

                    logger.info(
                        "Processed batch",
                        events=len(events),
                        successful=successful,
                        total_processed=self.processed_events,
                    )

                await asyncio.sleep(settings.event_processing_interval)

            except Exception as e:
                logger.error("Error in processing loop", error=str(e))
                await asyncio.sleep(5)

    async def _classify_event(self, event: LogEvent) -> "EventClassification":
        """Classify log event to determine ticket creation needs"""

        # Severity-based rules
        should_create = event.level in ["critical", "error"]

        # Service-based rules
        if event.service in ["payment", "authentication", "database"]:
            should_create = True

        # Pattern-based rules
        if any(
            keyword in event.message.lower()
            for keyword in ["timeout", "connection failed", "out of memory"]
        ):
            should_create = True

        # Frequency-based rules (rate limiting)
        recent_count = await self._get_recent_event_count(event)
        if recent_count > 10:  # Too many similar events
            should_create = False

        priority = settings.severity_mapping.get(event.level, "3")
        team = self._determine_team(event)
        system = settings.team_routing.get(team, "JIRA")

        return EventClassification(
            should_create_ticket=should_create,
            priority=priority,
            team=team,
            target_system=system,
            category=self._categorize_event(event),
        )

    def _generate_fingerprint(self, event: LogEvent) -> str:
        """Generate unique fingerprint for deduplication"""
        # Normalize error message (remove timestamps, IDs, etc.)
        normalized_message = self._normalize_message(event.message)

        fingerprint_data = {
            "service": event.service,
            "component": event.component or "",
            "level": event.level,
            "message_pattern": normalized_message[:200],  # Truncate
            "error_type": event.metadata.get("error_type", ""),
        }

        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]

    async def _check_existing_ticket(self, fingerprint: str) -> Optional[str]:
        """Check if ticket already exists for this incident"""
        if not self.redis:
            return None
        key = f"ticket_fingerprint:{fingerprint}"
        ticket_id = await self.redis.get(key)
        return ticket_id.decode() if ticket_id else None

    async def _store_ticket_fingerprint(self, fingerprint: str, ticket_id: str):
        """Store ticket fingerprint for deduplication"""
        if not self.redis:
            return
        key = f"ticket_fingerprint:{fingerprint}"
        await self.redis.setex(key, settings.duplicate_detection_window, ticket_id)

    def _normalize_message(self, message: str) -> str:
        """Normalize message for fingerprinting"""
        import re

        # Remove timestamps, IDs, numbers
        normalized = re.sub(
            r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", "TIMESTAMP", message
        )
        normalized = re.sub(
            r"\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b",
            "UUID",
            normalized,
        )
        normalized = re.sub(r"\b\d+\b", "NUMBER", normalized)
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized.strip().lower()

    def _determine_team(self, event: LogEvent) -> str:
        """Determine responsible team based on event"""
        service_teams = {
            "database": "database",
            "redis": "database",
            "api": "api",
            "web": "api",
            "auth": "security",
            "payment": "security",
            "infrastructure": "infrastructure",
        }

        return service_teams.get(event.service, "api")

    async def _update_existing_ticket(self, ticket_id: str, event: LogEvent):
        """Update existing ticket with new event information"""
        try:
            update_data = {
                "comment": f"Additional occurrence: {event.message}",
                "additional_events": [event.id],
            }
            # Determine system from ticket_id format
            system = (
                "JIRA"
                if ticket_id.startswith("DEMO-") or "-" in ticket_id
                else "ServiceNow"
            )
            await self.ticket_service.update_ticket(ticket_id, system, update_data)
            logger.info(
                "Updated existing ticket", ticket_id=ticket_id, event_id=event.id
            )
        except Exception as e:
            logger.error("Failed to update ticket", ticket_id=ticket_id, error=str(e))

    async def _create_ticket_request(
        self, event: LogEvent, classification: "EventClassification"
    ) -> "TicketRequest":
        """Create ticket request from event and classification"""
        from models.ticket import TicketRequest

        title = f"{event.level.upper()}: {event.service} - {event.message[:100]}"
        description = f"""
Service: {event.service}
Component: {event.component or 'N/A'}
Level: {event.level}
Message: {event.message}
Timestamp: {event.timestamp}
Host: {event.host or 'N/A'}
Request ID: {event.request_id or 'N/A'}

Stack Trace:
{event.stack_trace or 'N/A'}

Error Code: {event.error_code or 'N/A'}
        """.strip()

        return TicketRequest(
            title=title,
            description=description,
            system=classification.target_system,
            priority=classification.priority,
            category=classification.category,
            team=classification.team,
            tags=[event.service, event.level, classification.category],
            metadata={
                "component": event.component,
                "host": event.host,
                "request_id": event.request_id,
                "error_code": event.error_code,
            },
            source_event_id=event.id,
            fingerprint=self._generate_fingerprint(event),
        )

    async def _get_recent_event_count(self, event: LogEvent) -> int:
        """Get count of recent similar events"""
        if not self.redis:
            return 0
        try:
            # Use fingerprint to count recent events
            fingerprint = self._generate_fingerprint(event)
            key = f"event_count:{fingerprint}"
            count = await self.redis.get(key)
            return int(count.decode()) if count else 0
        except Exception:
            return 0

    def _categorize_event(self, event: LogEvent) -> str:
        """Categorize event based on service and message"""
        if "database" in event.service.lower() or "db" in event.service.lower():
            return "database"
        elif "api" in event.service.lower() or "web" in event.service.lower():
            return "api"
        elif "auth" in event.service.lower() or "security" in event.service.lower():
            return "security"
        elif "payment" in event.service.lower():
            return "payment"
        elif (
            "infrastructure" in event.service.lower()
            or "cache" in event.service.lower()
        ):
            return "infrastructure"
        else:
            return "general"

    async def _get_pending_events(self) -> List[LogEvent]:
        """Get pending events from Redis queue"""
        events: List[LogEvent] = []
        if not self.redis:
            return events
        for _ in range(settings.event_batch_size):
            event_data = await self.redis.lpop("events:pending")
            if not event_data:
                break
            try:
                event_dict = json.loads(event_data)
                event = LogEvent(**event_dict)
                events.append(event)
            except Exception as e:
                logger.error("Failed to parse event", error=str(e))

        return events


class EventClassification:
    """Result of event classification"""

    def __init__(
        self,
        should_create_ticket: bool,
        priority: str,
        team: str,
        target_system: str,
        category: str,
    ):
        self.should_create_ticket = should_create_ticket
        self.priority = priority
        self.team = team
        self.target_system = target_system
        self.category = category
