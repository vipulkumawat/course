from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any
import json
from datetime import datetime
import os

router = APIRouter()
# Use absolute path to templates directory
current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, "..", "..", "templates")
templates = Jinja2Templates(directory=template_dir)

@router.get("/correlations")
async def get_correlations(request: Request, limit: int = 100):
    """Get recent correlations"""
    correlation_engine = request.app.state.correlation_engine
    correlations = await correlation_engine.get_correlations(limit)
    
    # Convert to serializable format
    result = []
    for corr in correlations:
        result.append({
            "event_a": corr.event_a,
            "event_b": corr.event_b,
            "correlation_type": corr.correlation_type,
            "strength": corr.strength,
            "confidence": corr.confidence,
            "timestamp": corr.timestamp.isoformat(),
            "window_seconds": corr.window_seconds
        })
    
    return {"correlations": result}

@router.get("/correlations/stats")
async def get_correlation_stats(request: Request):
    """Get correlation statistics"""
    correlation_engine = request.app.state.correlation_engine
    stats = await correlation_engine.get_correlation_stats()
    return stats

@router.get("/correlations/types/{correlation_type}")
async def get_correlations_by_type(request: Request, correlation_type: str, limit: int = 50):
    """Get correlations by type"""
    correlation_engine = request.app.state.correlation_engine
    all_correlations = await correlation_engine.get_correlations(1000)
    
    filtered = [c for c in all_correlations if c.correlation_type == correlation_type]
    limited = filtered[:limit]
    
    result = []
    for corr in limited:
        result.append({
            "event_a": corr.event_a,
            "event_b": corr.event_b,
            "correlation_type": corr.correlation_type,
            "strength": corr.strength,
            "confidence": corr.confidence,
            "timestamp": corr.timestamp.isoformat(),
            "window_seconds": corr.window_seconds
        })
    
    return {"correlations": result}

@router.get("/logs/recent")
async def get_recent_logs(request: Request, count: int = 50):
    """Get recent log events"""
    log_collector = request.app.state.log_collector
    events = await log_collector.get_events(count)
    
    result = []
    for event in events:
        result.append({
            "timestamp": event.timestamp.isoformat(),
            "source": event.source,
            "service": event.service,
            "level": event.level,
            "message": event.message,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "correlation_id": event.correlation_id,
            "metrics": event.metrics
        })
    
    return {"events": result}

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Correlation analysis dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})
