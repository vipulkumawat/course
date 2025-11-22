"""Ticket data models"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TicketRequest(BaseModel):
    """Request to create a ticket"""

    title: str = Field(..., description="Ticket title/summary")
    description: str = Field(..., description="Detailed description")
    system: str = Field(..., description="Target system (JIRA/ServiceNow)")
    priority: str = Field(..., description="Priority level")

    # Classification
    category: str = Field(..., description="Issue category")
    team: str = Field(..., description="Responsible team")

    # Additional data
    tags: List[str] = Field(default_factory=list, description="Tags/labels")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    # Source event reference
    source_event_id: str = Field(..., description="Source log event ID")
    fingerprint: str = Field(..., description="Deduplication fingerprint")


class TicketResponse(BaseModel):
    """Response from ticket creation"""

    ticket_id: str = Field(..., description="Created ticket ID")
    system: str = Field(..., description="System where ticket was created")
    url: Optional[str] = Field(None, description="Ticket URL")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TicketUpdate(BaseModel):
    """Update to existing ticket"""

    ticket_id: str
    system: str
    comment: Optional[str] = None
    status_change: Optional[str] = None
    additional_events: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TicketStats(BaseModel):
    """Ticket creation statistics"""

    total_created: int = 0
    jira_tickets: int = 0
    servicenow_tickets: int = 0
    by_priority: Dict[str, int] = Field(default_factory=dict)
    by_team: Dict[str, int] = Field(default_factory=dict)
    last_24h: int = 0
