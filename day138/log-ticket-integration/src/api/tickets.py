"""Ticket management API routes"""

from fastapi import APIRouter, HTTPException, Depends
import structlog

from src.models.ticket import TicketRequest, TicketResponse, TicketStats, TicketUpdate
from src.services.ticket_service import TicketService

logger = structlog.get_logger()
router = APIRouter()


# Dependency injection for ticket service
async def get_ticket_service() -> TicketService:
    from src.main import ticket_service

    if not ticket_service:
        raise HTTPException(status_code=503, detail="Ticket service not available")
    return ticket_service


@router.post("/create", response_model=TicketResponse)
async def create_ticket(
    request: TicketRequest, service: TicketService = Depends(get_ticket_service)
) -> TicketResponse:
    """Create a new ticket in JIRA or ServiceNow"""

    ticket_id = await service.create_ticket(request)

    if not ticket_id:
        raise HTTPException(status_code=500, detail="Failed to create ticket")

    # Generate URL based on system
    url = None
    if request.system.upper() == "JIRA":
        url = f"https://demo-jira.atlassian.net/browse/{ticket_id}"
    elif request.system.upper() == "SERVICENOW":
        url = (
            f"https://demo.service-now.com/nav_to.do?uri=incident.do?sys_id={ticket_id}"
        )

    return TicketResponse(ticket_id=ticket_id, system=request.system, url=url)


@router.put("/{ticket_id}/update")
async def update_ticket(
    ticket_id: str,
    update: TicketUpdate,
    service: TicketService = Depends(get_ticket_service),
) -> dict:
    """Update an existing ticket"""

    success = await service.update_ticket(
        ticket_id,
        update.system,
        {
            "comment": update.comment,
            "status": update.status_change,
            "additional_events": update.additional_events,
        },
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update ticket")

    return {"message": "Ticket updated successfully", "ticket_id": ticket_id}


@router.get("/stats", response_model=TicketStats)
async def get_ticket_stats(
    service: TicketService = Depends(get_ticket_service),
) -> TicketStats:
    """Get ticket creation statistics"""

    stats = await service.get_ticket_stats()
    return TicketStats(**stats)


@router.get("/templates")
async def get_ticket_templates() -> dict:
    """Get available ticket templates"""

    templates = {
        "database_error": {
            "title": "Database Error: {service} - {error_type}",
            "description": """
Service: {service}
Component: {component}
Error: {message}
Timestamp: {timestamp}
Host: {host}

Stack Trace:
{stack_trace}

Impact: {impact_assessment}
Suggested Action: {suggested_action}
            """,
            "priority": "2",
            "tags": ["database", "production"],
        },
        "api_timeout": {
            "title": "API Timeout: {service} endpoint {endpoint}",
            "description": """
Service: {service}
Endpoint: {endpoint}
Timeout Duration: {timeout_duration}
Request ID: {request_id}
User Impact: {user_impact}

Recent Occurrences: {recent_count}
Performance Metrics: {metrics}
            """,
            "priority": "3",
            "tags": ["api", "performance"],
        },
        "infrastructure_alert": {
            "title": "Infrastructure Alert: {service} - {alert_type}",
            "description": """
Service: {service}
Alert Type: {alert_type}
Severity: {severity}
Component: {component}
Message: {message}
Timestamp: {timestamp}
Host: {host}

Infrastructure Details:
{infrastructure_details}

Impact Assessment: {impact_assessment}
Recommended Action: {recommended_action}
            """,
            "priority": "1",
            "tags": ["infrastructure", "system"],
        },
    }

    return {"templates": templates}
