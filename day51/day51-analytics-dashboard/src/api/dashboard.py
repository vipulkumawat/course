import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
import pandas as pd

from src.analytics.processor import AnalyticsProcessor
from src.websocket.manager import websocket_manager

router = APIRouter()

# Initialize analytics processor
analytics = AnalyticsProcessor("redis://localhost:6379/0")

class MetricRequest(BaseModel):
    service: str
    metric_name: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class DashboardConfig(BaseModel):
    layout: Dict[str, Any]
    refresh_interval: int = 5000
    time_range: int = 3600

@router.get("/metrics/{service}/{metric_name}")
async def get_metrics(
    service: str,
    metric_name: str,
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    limit: int = Query(1000, le=10000)
):
    """Get historical metrics for a service and metric name"""
    try:
        start_dt = None
        end_dt = None
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        metrics = await analytics.get_metrics(service, metric_name, start_dt, end_dt)
        
        # Limit results
        if len(metrics) > limit:
            # Sample data evenly
            step = len(metrics) // limit
            metrics = metrics[::step][:limit]
        
        return {
            "service": service,
            "metric_name": metric_name,
            "data_points": len(metrics),
            "metrics": metrics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends/{service}")
async def get_service_trends(service: str, window_minutes: int = Query(5, ge=1, le=60)):
    """Get trend analysis for all metrics of a service"""
    try:
        # Get recent metrics for trend calculation
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=window_minutes)
        
        # Get all available metrics for the service (simplified)
        metric_names = ['response_time', 'error_count', 'request_count']
        all_metrics = []
        
        for metric_name in metric_names:
            metrics = await analytics.get_metrics(service, metric_name, start_time, end_time)
            all_metrics.extend([
                {'timestamp': m['timestamp'], 'service': service, 'metric_name': metric_name, 'value': m['value']}
                for m in metrics
            ])
        
        # Convert to MetricPoint objects for trend calculation
        from src.analytics.processor import MetricPoint
        metric_points = [
            MetricPoint(
                timestamp=datetime.fromisoformat(m['timestamp']),
                service=m['service'],
                metric_name=m['metric_name'],
                value=m['value']
            )
            for m in all_metrics
        ]
        
        trends = await analytics.calculate_trends(metric_points, window_minutes)
        
        return {
            "service": service,
            "window_minutes": window_minutes,
            "trends": trends,
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/anomalies")
async def get_anomalies(
    service: Optional[str] = Query(None),
    hours: int = Query(1, ge=1, le=24),
    threshold: float = Query(2.0, ge=1.0, le=5.0)
):
    """Get detected anomalies"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Get metrics for anomaly detection
        services = [service] if service else ['web', 'api', 'database']  # Default services
        all_metrics = []
        
        for svc in services:
            for metric_name in ['response_time', 'error_count', 'request_count']:
                metrics = await analytics.get_metrics(svc, metric_name, start_time, end_time)
                all_metrics.extend([
                    {'timestamp': m['timestamp'], 'service': svc, 'metric_name': metric_name, 'value': m['value']}
                    for m in metrics
                ])
        
        # Convert to MetricPoint objects
        from src.analytics.processor import MetricPoint
        metric_points = [
            MetricPoint(
                timestamp=datetime.fromisoformat(m['timestamp']),
                service=m['service'],
                metric_name=m['metric_name'],
                value=m['value']
            )
            for m in all_metrics
        ]
        
        anomalies = await analytics.detect_anomalies(metric_points, threshold)
        
        return {
            "anomalies": anomalies,
            "detection_threshold": threshold,
            "time_range_hours": hours,
            "total_anomalies": len(anomalies)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services")
async def get_available_services():
    """Get list of available services"""
    # In production, this would query your service registry
    return {
        "services": [
            {"name": "web", "description": "Web frontend service"},
            {"name": "api", "description": "REST API service"},
            {"name": "database", "description": "Database service"},
            {"name": "cache", "description": "Redis cache service"},
            {"name": "auth", "description": "Authentication service"}
        ]
    }

@router.get("/dashboard-stats")
async def get_dashboard_stats():
    """Get real-time dashboard statistics"""
    try:
        # Get WebSocket connection stats
        ws_stats = websocket_manager.get_connection_stats()
        
        # Get recent metrics count
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=5)
        
        total_metrics = 0
        services = ['web', 'api', 'database']
        
        for service in services:
            for metric_name in ['response_time', 'error_count', 'request_count']:
                metrics = await analytics.get_metrics(service, metric_name, start_time, end_time)
                total_metrics += len(metrics)
        
        return {
            "websocket_connections": ws_stats['total_connections'],
            "active_subscriptions": sum(ws_stats['subscriptions'].values()),
            "recent_metrics_count": total_metrics,
            "uptime_minutes": 60,  # Placeholder
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def generate_sample_metrics():
    """Generate sample metrics for demonstration"""
    import random
    import numpy as np
    
    services = ['web', 'api', 'database']
    current_time = datetime.now()
    
    sample_metrics = []
    
    for i in range(100):  # Generate 100 sample points
        timestamp = current_time - timedelta(minutes=i)
        
        for service in services:
            # Response time (normally distributed around service baseline)
            baselines = {'web': 50, 'api': 30, 'database': 100}
            response_time = max(1, np.random.normal(baselines[service], 15))
            
            sample_metrics.append({
                'timestamp': timestamp.isoformat(),
                'service': service,
                'metric_name': 'response_time',
                'value': response_time,
                'tags': {'endpoint': f'/{service}/health'}
            })
            
            # Error count (Poisson distribution)
            error_count = np.random.poisson(0.5)
            if error_count > 0:
                sample_metrics.append({
                    'timestamp': timestamp.isoformat(),
                    'service': service,
                    'metric_name': 'error_count',
                    'value': float(error_count),
                    'tags': {'error_type': 'timeout'}
                })
            
            # Request count
            request_count = max(1, np.random.poisson(10))
            sample_metrics.append({
                'timestamp': timestamp.isoformat(),
                'service': service,
                'metric_name': 'request_count',
                'value': float(request_count),
                'tags': {'method': 'GET', 'status': '200'}
            })
    
    return sample_metrics

@router.post("/generate-sample-data")
async def generate_sample_data(background_tasks: BackgroundTasks):
    """Generate sample metrics for testing"""
    try:
        # Generate sample data
        sample_data = await generate_sample_metrics()
        
        # Convert to MetricPoint objects and store
        from src.analytics.processor import MetricPoint
        metric_points = []
        
        for data in sample_data:
            metric_points.append(MetricPoint(
                timestamp=datetime.fromisoformat(data['timestamp']),
                service=data['service'],
                metric_name=data['metric_name'],
                value=data['value'],
                tags=data.get('tags', {})
            ))
        
        # Store metrics
        await analytics.store_metrics(metric_points)
        
        # Broadcast update to connected clients
        await websocket_manager.broadcast({
            'type': 'metrics_update',
            'message': f'Generated {len(metric_points)} sample metrics',
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            "message": "Sample data generated successfully",
            "metrics_count": len(metric_points),
            "services": list(set(m.service for m in metric_points))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 