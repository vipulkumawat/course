"""FastAPI application for incident response system"""
import asyncio
import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

from src.playbooks.engine.playbook_engine import PlaybookEngine
from src.playbooks.response_coordinator import ResponseCoordinator, SecurityEvent
from src.actions.network.network_actions import BlockIPAction, IsolateSystemAction, CaptureTrafficAction
from src.actions.identity.identity_actions import SuspendAccountAction, ForcePasswordResetAction, RevokeSessionsAction
from src.actions.alert.alert_actions import SendEmailAlertAction, SendSlackAlertAction, CreatePagerDutyIncidentAction
from src.actions.evidence.evidence_actions import CreateSystemSnapshotAction, PreserveLogsAction, CollectArtifactsAction

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Initialize FastAPI
app = FastAPI(
    title="Automated Incident Response System",
    description="Security incident response orchestration platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files path for dashboard
static_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'static')
dashboard_html = os.path.join(static_path, 'index.html') if os.path.exists(static_path) else None

# Global instances
playbook_engine: Optional[PlaybookEngine] = None
response_coordinator: Optional[ResponseCoordinator] = None
coordinator_task: Optional[asyncio.Task] = None


# Pydantic models
class SecurityEventRequest(BaseModel):
    event_type: str
    severity: str
    source: str
    details: Dict[str, Any]
    ioc_data: Optional[Dict[str, Any]] = None


class PlaybookExecutionRequest(BaseModel):
    template_name: str
    context: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global playbook_engine, response_coordinator, coordinator_task
    
    logger.info("initializing_incident_response_system")
    
    # Create action registry
    action_registry = {
        'block_ip': BlockIPAction(),
        'isolate_system': IsolateSystemAction(),
        'capture_traffic': CaptureTrafficAction(),
        'suspend_account': SuspendAccountAction(),
        'force_password_reset': ForcePasswordResetAction(),
        'revoke_sessions': RevokeSessionsAction(),
        'send_email_alert': SendEmailAlertAction(),
        'send_slack_alert': SendSlackAlertAction(),
        'create_pagerduty': CreatePagerDutyIncidentAction(),
        'create_snapshot': CreateSystemSnapshotAction(),
        'preserve_logs': PreserveLogsAction(),
        'collect_artifacts': CollectArtifactsAction()
    }
    
    # Initialize playbook engine
    playbook_engine = PlaybookEngine(action_registry)
    
    # Load playbook templates
    import glob
    import os
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'playbooks', 'templates')
    for template_path in glob.glob(os.path.join(template_dir, '*.yaml')):
        playbook_engine.load_playbook_template(template_path)
    
    # Initialize response coordinator
    response_coordinator = ResponseCoordinator(playbook_engine)
    
    # Start coordinator in background
    coordinator_task = asyncio.create_task(response_coordinator.start())
    
    logger.info("incident_response_system_ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global response_coordinator, coordinator_task
    
    logger.info("shutting_down_incident_response_system")
    
    if response_coordinator:
        await response_coordinator.stop()
    
    if coordinator_task:
        coordinator_task.cancel()


@app.post("/api/events", status_code=202)
async def submit_security_event(event_request: SecurityEventRequest):
    """Submit a security event for automated response"""
    event = SecurityEvent(
        event_id=f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        event_type=event_request.event_type,
        severity=event_request.severity,
        source=event_request.source,
        timestamp=datetime.now(),
        details=event_request.details,
        ioc_data=event_request.ioc_data
    )
    
    event_id = await response_coordinator.handle_security_event(event)
    
    return {
        'event_id': event_id,
        'status': 'accepted',
        'message': 'Security event accepted for processing'
    }


@app.post("/api/playbooks/execute")
async def execute_playbook(request: PlaybookExecutionRequest):
    """Manually execute a playbook"""
    import uuid
    
    try:
        playbook = playbook_engine.create_playbook_from_template(
            request.template_name,
            request.context
        )
        
        execution_id = str(uuid.uuid4())
        result = await playbook_engine.execute_playbook(playbook, execution_id)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/playbooks/templates")
async def list_playbook_templates():
    """List available playbook templates"""
    return {
        'templates': list(playbook_engine.playbook_templates.keys())
    }


@app.get("/api/responses/{execution_id}")
async def get_response_status(execution_id: str):
    """Get status of incident response"""
    status = response_coordinator.get_response_status(execution_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Response not found")
    
    return status


@app.get("/api/responses")
async def list_responses(limit: int = 50):
    """List recent incident responses"""
    history = response_coordinator.get_response_history(limit)
    return {'responses': history}


@app.get("/api/audit-log")
async def get_audit_log(execution_id: Optional[str] = None, limit: int = 100):
    """Get audit log entries"""
    log_entries = playbook_engine.get_audit_log(execution_id)
    return {'audit_log': log_entries[-limit:]}


@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics"""
    return {
        'active_playbooks': len(playbook_engine.active_playbooks),
        'total_responses': len(response_coordinator.response_history),
        'audit_entries': len(playbook_engine.audit_log),
        'playbook_templates': len(playbook_engine.playbook_templates)
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }


@app.post("/api/playbooks/{execution_id}/rollback")
async def rollback_playbook(execution_id: str):
    """Rollback a playbook execution"""
    try:
        result = await playbook_engine.rollback_playbook(execution_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/approvals/{approval_id}/approve")
async def approve_action(approval_id: str, approved: bool, approver: str, reason: Optional[str] = None):
    """Approve or reject an action"""
    try:
        playbook_engine.approve_action(approval_id, approver, approved, reason)
        return {
            'approval_id': approval_id,
            'status': 'approved' if approved else 'rejected',
            'approver': approver
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/approvals")
async def list_pending_approvals():
    """List pending approval requests"""
    approvals = []
    for req_id, approval in playbook_engine.pending_approvals.items():
        if approval.status.value == 'pending':
            approvals.append({
                'request_id': approval.request_id,
                'action_name': approval.action_name,
                'action_type': approval.action_type,
                'requested_at': approval.requested_at.isoformat(),
                'approvers': approval.approvers,
                'status': approval.status.value
            })
    return {'approvals': approvals}


@app.post("/api/incidents/{execution_id}/report")
async def generate_incident_report(execution_id: str, incident_data: Dict[str, Any]):
    """Generate incident report"""
    try:
        report = playbook_engine.generate_incident_report(execution_id, incident_data)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/incidents/reports")
async def get_incident_reports(limit: int = 50):
    """Get incident reports"""
    reports = playbook_engine.get_incident_reports(limit)
    return {'reports': reports}


@app.get("/api/sla/status")
async def get_sla_status():
    """Get SLA status across all playbooks"""
    sla_stats = {
        'total_playbooks': len(playbook_engine.active_playbooks),
        'sla_met': 0,
        'sla_breached': 0,
        'average_response_time': 0.0,
        'average_resolution_time': 0.0
    }
    
    response_times = []
    resolution_times = []
    
    for playbook in playbook_engine.active_playbooks.values():
        if playbook.sla:
            if playbook.sla.sla_met:
                sla_stats['sla_met'] += 1
            else:
                sla_stats['sla_breached'] += 1
            
            if playbook.sla.actual_response_time:
                response_times.append(playbook.sla.actual_response_time)
            if playbook.sla.actual_resolution_time:
                resolution_times.append(playbook.sla.actual_resolution_time)
    
    if response_times:
        sla_stats['average_response_time'] = sum(response_times) / len(response_times)
    if resolution_times:
        sla_stats['average_resolution_time'] = sum(resolution_times) / len(resolution_times)
    
    return sla_stats


@app.get("/")
async def serve_dashboard():
    """Serve the dashboard HTML"""
    if dashboard_html and os.path.exists(dashboard_html):
        return FileResponse(dashboard_html)
    return {"message": "Dashboard not found. Please ensure index.html exists in src/dashboard/static/"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
