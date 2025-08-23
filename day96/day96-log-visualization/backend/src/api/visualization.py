from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import asyncio
from datetime import datetime
from ..services.chart_service import ChartDataService
from ..models.log_models import TimeSeriesData, HeatmapData, DashboardMetrics
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/visualization", tags=["visualization"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected", connections=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected", connections=len(self.active_connections))
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections[:]:  # Create copy to avoid modification during iteration
            try:
                await connection.send_text(json.dumps(message, default=str))
            except:
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Dependency to get database session
def get_db():
    # For demo purposes, we don't need a real database session
    # The chart service now uses demo data directly
    return None

@router.get("/error-trends", response_model=List[TimeSeriesData])
async def get_error_trends(
    hours: int = 24,
    services: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get error rate trends over time for specified services"""
    try:
        service_list = services.split(',') if services else None
        chart_service = ChartDataService(db)
        trends = await chart_service.get_error_rate_trends(hours, service_list)
        return trends
    except Exception as e:
        logger.error("Error fetching error trends", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch error trends")

@router.get("/response-time-heatmap", response_model=HeatmapData)
async def get_response_time_heatmap(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get response time heatmap data"""
    try:
        chart_service = ChartDataService(db)
        heatmap = await chart_service.get_response_time_heatmap(hours)
        return heatmap
    except Exception as e:
        logger.error("Error fetching heatmap data", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch heatmap data")

@router.get("/service-performance")
async def get_service_performance(
    hours: int = 1,
    db: Session = Depends(get_db)
):
    """Get recent service performance metrics for bar charts"""
    try:
        chart_service = ChartDataService(db)
        performance = await chart_service.get_service_performance_bars(hours)
        return performance
    except Exception as e:
        logger.error("Error fetching service performance", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch service performance")

@router.get("/real-time-metrics", response_model=DashboardMetrics)
async def get_real_time_metrics(db: Session = Depends(get_db)):
    """Get current dashboard metrics"""
    try:
        chart_service = ChartDataService(db)
        metrics = await chart_service.get_real_time_metrics()
        return metrics
    except Exception as e:
        logger.error("Error fetching real-time metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

@router.websocket("/real-time")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time chart updates"""
    await manager.connect(websocket)
    try:
        # Send initial data
        chart_service = ChartDataService(db)
        initial_metrics = await chart_service.get_real_time_metrics()
        await websocket.send_text(json.dumps({
            "type": "metrics_update",
            "data": initial_metrics.dict()
        }, default=str))
        
        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(5)  # Update every 5 seconds
            try:
                metrics = await chart_service.get_real_time_metrics()
                await manager.broadcast({
                    "type": "metrics_update",
                    "data": metrics.dict()
                })
            except Exception as e:
                logger.error("Error in WebSocket update", error=str(e))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        manager.disconnect(websocket)
