"""
API routes for alerts management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from app.core.database import get_db
from models.schemas import Alert, SavedSearch
from models.pydantic_models import AlertCreate, AlertUpdate, AlertResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    user_id: str = Query("demo_user", description="User ID"),
    active_only: bool = Query(False, description="Filter active alerts only"),
    db: Session = Depends(get_db)
):
    """Get all alerts for a user"""
    try:
        query = db.query(Alert).filter(Alert.user_id == user_id)
        
        if active_only:
            query = query.filter(Alert.is_active == True)
        
        alerts = query.order_by(Alert.created_at.desc()).all()
        return [AlertResponse.from_orm(alert) for alert in alerts]
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Get a specific alert by ID"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse.from_orm(alert)

@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Create a new alert"""
    try:
        # Verify saved search exists and belongs to user
        saved_search = db.query(SavedSearch).filter(
            SavedSearch.id == alert_data.saved_search_id,
            SavedSearch.user_id == user_id
        ).first()
        
        if not saved_search:
            raise HTTPException(
                status_code=404, 
                detail="Saved search not found or access denied"
            )
        
        # Check for duplicate alert names
        existing = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.name == alert_data.name
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Alert name already exists")
        
        new_alert = Alert(
            name=alert_data.name,
            description=alert_data.description,
            user_id=user_id,
            saved_search_id=alert_data.saved_search_id,
            condition_type=alert_data.condition_type.value,
            threshold_value=alert_data.threshold_value,
            comparison_operator=alert_data.comparison_operator.value if alert_data.comparison_operator else None,
            time_window_minutes=alert_data.time_window_minutes,
            notification_channels=[ch.value for ch in alert_data.notification_channels],
            notification_emails=alert_data.notification_emails,
            webhook_url=alert_data.webhook_url,
            cooldown_minutes=alert_data.cooldown_minutes
        )
        
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)
        
        logger.info(f"Created alert: {new_alert.name} for user: {user_id}")
        return AlertResponse.from_orm(new_alert)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create alert")

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    alert_data: AlertUpdate,
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Update an existing alert"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    try:
        # Update only provided fields
        update_data = alert_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "condition_type" and value:
                setattr(alert, field, value.value)
            elif field == "comparison_operator" and value:
                setattr(alert, field, value.value)
            elif field == "notification_channels" and value:
                setattr(alert, field, [ch.value for ch in value])
            else:
                setattr(alert, field, value)
        
        alert.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Updated alert: {alert.name}")
        return AlertResponse.from_orm(alert)
        
    except Exception as e:
        logger.error(f"Error updating alert: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update alert")

@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Delete an alert"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    try:
        db.delete(alert)
        db.commit()
        logger.info(f"Deleted alert: {alert.name}")
        return {"message": "Alert deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete alert")

@router.post("/{alert_id}/toggle")
async def toggle_alert(
    alert_id: str,
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Toggle alert active/inactive status"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    try:
        alert.is_active = not alert.is_active
        alert.updated_at = datetime.utcnow()
        db.commit()
        
        status = "activated" if alert.is_active else "deactivated"
        logger.info(f"Alert {alert.name} {status}")
        
        return {
            "message": f"Alert {status} successfully",
            "is_active": alert.is_active
        }
        
    except Exception as e:
        logger.error(f"Error toggling alert: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to toggle alert")

@router.post("/{alert_id}/test")
async def test_alert(
    alert_id: str,
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Test alert by sending a test notification"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    try:
        # Mock test notification
        test_result = {
            "alert_id": alert_id,
            "alert_name": alert.name,
            "test_timestamp": datetime.utcnow().isoformat(),
            "notification_channels": alert.notification_channels,
            "test_results": []
        }
        
        for channel in alert.notification_channels:
            if channel == "email":
                test_result["test_results"].append({
                    "channel": "email",
                    "status": "sent",
                    "recipients": alert.notification_emails,
                    "message": "Test alert notification sent successfully"
                })
            elif channel == "webhook":
                test_result["test_results"].append({
                    "channel": "webhook",
                    "status": "sent",
                    "webhook_url": alert.webhook_url,
                    "message": "Test webhook notification sent successfully"
                })
            elif channel == "in_app":
                test_result["test_results"].append({
                    "channel": "in_app",
                    "status": "sent",
                    "message": "Test in-app notification sent successfully"
                })
        
        logger.info(f"Test notification sent for alert: {alert.name}")
        return test_result
        
    except Exception as e:
        logger.error(f"Error testing alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to test alert")

@router.get("/{alert_id}/history")
async def get_alert_history(
    alert_id: str,
    user_id: str = Query("demo_user", description="User ID"),
    limit: int = Query(50, description="Number of notifications to return"),
    db: Session = Depends(get_db)
):
    """Get alert notification history"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    try:
        from models.schemas import Notification
        
        notifications = db.query(Notification).filter(
            Notification.alert_id == alert_id
        ).order_by(Notification.created_at.desc()).limit(limit).all()
        
        return {
            "alert_id": alert_id,
            "alert_name": alert.name,
            "total_triggers": alert.trigger_count,
            "last_triggered": alert.last_triggered,
            "notifications": [
                {
                    "id": notif.id,
                    "title": notif.title,
                    "message": notif.message,
                    "channel": notif.channel,
                    "status": notif.status,
                    "created_at": notif.created_at,
                    "sent_at": notif.sent_at,
                    "delivered_at": notif.delivered_at,
                    "error_message": notif.error_message
                }
                for notif in notifications
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert history")
