"""Ticket creation service for JIRA and ServiceNow integration"""

import json
from typing import Dict, Optional
import httpx
import structlog
import redis.asyncio as aioredis
from jinja2 import Environment, BaseLoader

from src.models.ticket import TicketRequest
from src.utils.config import settings

logger = structlog.get_logger()


class TicketService:
    """Unified ticket creation service"""

    def __init__(self):
        self.jira_client = None
        self.servicenow_client = None
        self.template_env = Environment(loader=BaseLoader())
        self.connected = False
        self.redis = None

    async def initialize(self):
        """Initialize HTTP clients"""
        timeout = httpx.Timeout(30.0)

        # JIRA client with basic auth
        jira_auth = (settings.jira_username, settings.jira_api_token)
        self.jira_client = httpx.AsyncClient(
            base_url=settings.jira_url,
            auth=jira_auth,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

        # ServiceNow client with basic auth
        servicenow_auth = (settings.servicenow_username, settings.servicenow_password)
        self.servicenow_client = httpx.AsyncClient(
            base_url=settings.servicenow_url,
            auth=servicenow_auth,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

        # Initialize Redis connection for stats tracking
        self.redis = aioredis.from_url(settings.redis_url)
        
        # Initialize demo stats if they don't exist
        await self._initialize_demo_stats()

        self.connected = True
        logger.info("Ticket service initialized")

    async def close(self):
        """Close HTTP clients"""
        if self.jira_client:
            await self.jira_client.aclose()
        if self.servicenow_client:
            await self.servicenow_client.aclose()
        if self.redis:
            await self.redis.close()
        self.connected = False

    def is_connected(self) -> bool:
        """Check if service is connected"""
        return self.connected

    async def create_ticket(self, ticket_request: TicketRequest) -> Optional[str]:
        """Create ticket in appropriate system"""
        try:
            if ticket_request.system.upper() == "JIRA":
                return await self._create_jira_ticket(ticket_request)
            elif ticket_request.system.upper() == "SERVICENOW":
                return await self._create_servicenow_ticket(ticket_request)
            else:
                logger.error("Unknown ticket system", system=ticket_request.system)
                return None

        except Exception as e:
            logger.error(
                "Failed to create ticket", error=str(e), system=ticket_request.system
            )
            return None

    async def _create_jira_ticket(self, ticket_request: TicketRequest) -> Optional[str]:
        """Create JIRA issue"""

        # JIRA issue payload
        issue_data = {
            "fields": {
                "project": {"key": settings.jira_project_key},
                "summary": ticket_request.title,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": ticket_request.description}
                            ],
                        }
                    ],
                },
                "issuetype": {"name": "Bug"},
                "priority": {"id": ticket_request.priority},
                "labels": ticket_request.tags,
                "customfield_10000": ticket_request.metadata.get(
                    "component", ""
                ),  # Component field
            }
        }

        response = await self.jira_client.post("/rest/api/3/issue", json=issue_data)

        if response.status_code == 201:
            result = response.json()
            issue_key = result["key"]
            logger.info("Created JIRA issue", issue_key=issue_key)
            # Track stats
            await self._increment_ticket_stats("JIRA", ticket_request.priority)
            return issue_key
        else:
            logger.error(
                "JIRA API error", status=response.status_code, response=response.text
            )
            return None

    async def _create_servicenow_ticket(
        self, ticket_request: TicketRequest
    ) -> Optional[str]:
        """Create ServiceNow incident"""

        # ServiceNow incident payload
        incident_data = {
            "short_description": ticket_request.title,
            "description": ticket_request.description,
            "urgency": ticket_request.priority,
            "impact": ticket_request.priority,
            "category": ticket_request.metadata.get("category", "Software"),
            "subcategory": ticket_request.metadata.get("subcategory", "Application"),
            "state": "1",  # New
            "caller_id": settings.servicenow_username,
            "work_notes": json.dumps(ticket_request.metadata, indent=2),
        }

        response = await self.servicenow_client.post(
            f"/api/now/table/{settings.servicenow_table}", json=incident_data
        )

        if response.status_code == 201:
            result = response.json()
            incident_number = result["result"]["number"]
            logger.info("Created ServiceNow incident", incident_number=incident_number)
            # Track stats
            await self._increment_ticket_stats("SERVICENOW", ticket_request.priority)
            return incident_number
        else:
            logger.error(
                "ServiceNow API error",
                status=response.status_code,
                response=response.text,
            )
            return None

    async def update_ticket(
        self, ticket_id: str, system: str, update_data: Dict
    ) -> bool:
        """Update existing ticket with new information"""
        try:
            if system.upper() == "JIRA":
                return await self._update_jira_ticket(ticket_id, update_data)
            elif system.upper() == "SERVICENOW":
                return await self._update_servicenow_ticket(ticket_id, update_data)
            else:
                logger.error("Unknown ticket system for update", system=system)
                return False

        except Exception as e:
            logger.error("Failed to update ticket", ticket_id=ticket_id, error=str(e))
            return False

    async def _update_jira_ticket(self, issue_key: str, update_data: Dict) -> bool:
        """Update JIRA issue with additional information"""

        # Add comment to JIRA issue
        comment_data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": update_data.get(
                                    "comment", "Additional event information"
                                ),
                            }
                        ],
                    }
                ],
            }
        }

        response = await self.jira_client.post(
            f"/rest/api/3/issue/{issue_key}/comment", json=comment_data
        )

        return response.status_code == 201

    async def _update_servicenow_ticket(
        self, ticket_id: str, update_data: Dict
    ) -> bool:
        """Update ServiceNow incident with additional information"""

        incident_data = {
            "work_notes": update_data.get("comment", "Additional event information")
        }

        response = await self.servicenow_client.patch(
            f"/api/now/table/{settings.servicenow_table}/{ticket_id}",
            json=incident_data,
        )

        return response.status_code == 200

    async def _initialize_demo_stats(self):
        """Initialize demo statistics if they don't exist"""
        if not self.redis:
            return
        
        # Check if stats already exist
        total = await self.redis.get("stats:tickets:total")
        if total is None:
            # Set demo stats
            await self.redis.set("stats:tickets:total", 15)
            await self.redis.set("stats:tickets:jira", 9)
            await self.redis.set("stats:tickets:servicenow", 6)
            await self.redis.set("stats:tickets:last_24h", 8)
            # Priority stats
            await self.redis.set("stats:tickets:priority:1", 3)  # Critical
            await self.redis.set("stats:tickets:priority:2", 7)  # High
            await self.redis.set("stats:tickets:priority:3", 5)  # Medium
            logger.info("Initialized demo ticket statistics")

    async def _increment_ticket_stats(self, system: str, priority: str):
        """Increment ticket statistics in Redis"""
        if not self.redis:
            return
        
        try:
            # Increment total
            await self.redis.incr("stats:tickets:total")
            
            # Increment system-specific count
            if system.upper() == "JIRA":
                await self.redis.incr("stats:tickets:jira")
            elif system.upper() == "SERVICENOW":
                await self.redis.incr("stats:tickets:servicenow")
            
            # Increment priority count
            await self.redis.incr(f"stats:tickets:priority:{priority}")
            
            # Increment last 24h (simplified - in production would use time-based keys)
            await self.redis.incr("stats:tickets:last_24h")
        except Exception as e:
            logger.error("Failed to update ticket stats", error=str(e))

    async def get_ticket_stats(self) -> Dict:
        """Get ticket creation statistics from Redis"""
        stats = {
            "total_created": 0,
            "jira_tickets": 0,
            "servicenow_tickets": 0,
            "by_priority": {},
            "by_team": {},
            "last_24h": 0,
        }

        if not self.redis:
            return stats

        try:
            # Get basic stats
            total = await self.redis.get("stats:tickets:total")
            jira = await self.redis.get("stats:tickets:jira")
            servicenow = await self.redis.get("stats:tickets:servicenow")
            last_24h = await self.redis.get("stats:tickets:last_24h")

            stats["total_created"] = int(total) if total else 0
            stats["jira_tickets"] = int(jira) if jira else 0
            stats["servicenow_tickets"] = int(servicenow) if servicenow else 0
            stats["last_24h"] = int(last_24h) if last_24h else 0

            # Get priority stats
            for priority in ["1", "2", "3", "4", "5"]:
                count = await self.redis.get(f"stats:tickets:priority:{priority}")
                if count:
                    stats["by_priority"][priority] = int(count)

        except Exception as e:
            logger.error("Failed to get ticket stats", error=str(e))

        return stats
