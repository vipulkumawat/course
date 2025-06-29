"""Web interface for alert management."""
from fastapi import FastAPI, Request, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
import json
import asyncio
from datetime import datetime, timedelta

from config.database import get_db, Alert, AlertRule, LogEntry
from src.alert_engine.engine import AlertEngine
from src.alert_engine.notification import NotificationManager

app = FastAPI(title="Alert Generation System", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global alert engine instance
alert_engine = None
notification_manager = NotificationManager()

# WebSocket connections for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    global alert_engine
    alert_engine = AlertEngine()
    # Start alert engine in background
    asyncio.create_task(alert_engine.start())

@app.on_event("shutdown")
async def shutdown_event():
    if alert_engine:
        await alert_engine.stop()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page."""
    # Get recent alerts
    recent_alerts = db.query(Alert).order_by(Alert.last_occurrence.desc()).limit(10).all()
    
    # Get alert counts by severity
    alert_counts = {}
    for severity in ['low', 'medium', 'high', 'critical']:
        count = db.query(Alert).filter(
            Alert.severity == severity,
            Alert.state.in_(['NEW', 'ACKNOWLEDGED', 'ESCALATED'])
        ).count()
        alert_counts[severity] = count
    
    # Get total log count
    total_logs = db.query(LogEntry).count()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "recent_alerts": recent_alerts,
        "alert_counts": alert_counts,
        "total_logs": total_logs
    })

@app.get("/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    """Get all active alerts."""
    alerts = db.query(Alert).filter(
        Alert.state.in_(['NEW', 'ACKNOWLEDGED', 'ESCALATED'])
    ).order_by(Alert.last_occurrence.desc()).all()
    
    return [{
        "id": alert.id,
        "pattern_name": alert.pattern_name,
        "severity": alert.severity,
        "message": alert.message,
        "count": alert.count,
        "state": alert.state,
        "first_occurrence": alert.first_occurrence.isoformat(),
        "last_occurrence": alert.last_occurrence.isoformat(),
        "acknowledged_by": alert.acknowledged_by
    } for alert in alerts]

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.state = 'ACKNOWLEDGED'
    alert.acknowledged_by = 'web_user'
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    
    # Broadcast update
    await manager.broadcast(json.dumps({
        "type": "alert_acknowledged",
        "alert_id": alert_id
    }))
    
    return {"message": "Alert acknowledged"}

@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Resolve an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.state = 'RESOLVED'
    alert.resolved_at = datetime.utcnow()
    db.commit()
    
    # Broadcast update
    await manager.broadcast(json.dumps({
        "type": "alert_resolved",
        "alert_id": alert_id
    }))
    
    return {"message": "Alert resolved"}

@app.get("/rules")
async def get_rules(db: Session = Depends(get_db)):
    """Get all alert rules."""
    rules = db.query(AlertRule).all()
    return [{
        "id": rule.id,
        "name": rule.name,
        "pattern": rule.pattern,
        "threshold": rule.threshold,
        "window_seconds": rule.window_seconds,
        "severity": rule.severity,
        "enabled": rule.enabled
    } for rule in rules]

@app.post("/rules")
async def create_rule(rule_data: dict, db: Session = Depends(get_db)):
    """Create a new alert rule."""
    rule = AlertRule(
        name=rule_data['name'],
        pattern=rule_data['pattern'],
        threshold=rule_data['threshold'],
        window_seconds=rule_data['window_seconds'],
        severity=rule_data['severity']
    )
    db.add(rule)
    db.commit()
    
    # Reload patterns in alert engine
    if alert_engine:
        alert_engine.pattern_matcher.load_patterns()
    
    return {"message": "Rule created"}

@app.post("/test/inject_log")
async def inject_test_log(log_data: dict):
    """Inject a test log for demonstration."""
    if alert_engine:
        await alert_engine.inject_test_log(
            message=log_data.get('message', 'Test log message'),
            level=log_data.get('level', 'ERROR'),
            source=log_data.get('source', 'test')
        )
        return {"message": "Test log injected"}
    else:
        raise HTTPException(status_code=500, detail="Alert engine not running")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics."""
    total_alerts = db.query(Alert).count()
    active_alerts = db.query(Alert).filter(
        Alert.state.in_(['NEW', 'ACKNOWLEDGED', 'ESCALATED'])
    ).count()
    
    # Recent activity (last hour)
    cutoff_time = datetime.utcnow() - timedelta(hours=1)
    recent_alerts = db.query(Alert).filter(
        Alert.first_occurrence >= cutoff_time
    ).count()
    
    recent_logs = db.query(LogEntry).filter(
        LogEntry.timestamp >= cutoff_time
    ).count()
    
    # Get alert counts by severity
    alert_counts = {}
    for severity in ['low', 'medium', 'high', 'critical']:
        count = db.query(Alert).filter(
            Alert.severity == severity,
            Alert.state.in_(['NEW', 'ACKNOWLEDGED', 'ESCALATED'])
        ).count()
        alert_counts[severity] = count
    
    return {
        "total_alerts": total_alerts,
        "active_alerts": active_alerts,
        "recent_alerts": recent_alerts,
        "recent_logs": recent_logs,
        "alert_counts": alert_counts,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
