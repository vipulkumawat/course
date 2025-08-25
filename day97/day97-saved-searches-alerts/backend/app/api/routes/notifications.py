"""
API routes for notifications management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from models.schemas import Notification
from models.pydantic_models import NotificationResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    user_id: str = Query("demo_user", description="User ID"),
    unread_only: bool = Query(False, description="Show unread notifications only"),
    channel: Optional[str] = Query(None, description="Filter by notification channel"),
    limit: int = Query(50, description="Number of notifications to return"),
    db: Session = Depends(get_db)
):
    """Get notifications for a user"""
    try:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.delivered_at.is_(None))
        
        if channel:
            query = query.filter(Notification.channel == channel)
        
        notifications = query.order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
        
        return [NotificationResponse.from_orm(notif) for notif in notifications]
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notifications")

@router.post("/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    try:
        if not notification.delivered_at:
            notification.delivered_at = datetime.utcnow()
            db.commit()
        
        return {"message": "Notification marked as read"}
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

@router.post("/mark-all-read")
async def mark_all_notifications_read(
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for a user"""
    try:
        unread_notifications = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.delivered_at.is_(None)
        ).all()
        
        for notification in unread_notifications:
            notification.delivered_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": f"Marked {len(unread_notifications)} notifications as read"
        }
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to mark notifications as read")

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Delete a notification"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    try:
        db.delete(notification)
        db.commit()
        return {"message": "Notification deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete notification")

@router.get("/stats")
async def get_notification_stats(
    user_id: str = Query("demo_user", description="User ID"),
    days: int = Query(7, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get notification statistics for a user"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        notifications = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.created_at >= start_date
        ).all()
        
        total_notifications = len(notifications)
        unread_count = len([n for n in notifications if not n.delivered_at])
        
        # Group by channel
        channel_stats = {}
        for notif in notifications:
            channel = notif.channel
            if channel not in channel_stats:
                channel_stats[channel] = {"total": 0, "unread": 0}
            channel_stats[channel]["total"] += 1
            if not notif.delivered_at:
                channel_stats[channel]["unread"] += 1
        
        # Group by status
        status_stats = {}
        for notif in notifications:
            status = notif.status
            status_stats[status] = status_stats.get(status, 0) + 1
        
        return {
            "period_days": days,
            "total_notifications": total_notifications,
            "unread_count": unread_count,
            "read_count": total_notifications - unread_count,
            "channel_breakdown": channel_stats,
            "status_breakdown": status_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notification statistics")
