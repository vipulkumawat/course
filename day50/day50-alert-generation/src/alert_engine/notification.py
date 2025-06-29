"""Notification manager for sending alerts."""
import asyncio
import json
from typing import Dict, List
from datetime import datetime
import structlog
import httpx
from config.database import Alert
from config.settings import settings

logger = structlog.get_logger()

class NotificationManager:
    def __init__(self):
        self.channels = settings.NOTIFICATION_CHANNELS
        self.active_notifications = {}
    
    async def send_alert(self, alert):
        """Send notification for new alert."""
        # Handle both Alert objects and dict objects
        if isinstance(alert, dict):
            notification_data = {
                'alert_id': alert['id'],
                'pattern_name': alert['pattern_name'],
                'severity': alert['severity'],
                'message': alert['message'],
                'count': alert['count'],
                'timestamp': alert['first_occurrence'],
                'state': alert['state']
            }
        else:
            notification_data = {
                'alert_id': alert.id,
                'pattern_name': alert.pattern_name,
                'severity': alert.severity,
                'message': alert.message,
                'count': alert.count,
                'timestamp': alert.first_occurrence.isoformat(),
                'state': alert.state
            }
        
        logger.info("Sending alert notification", alert_id=notification_data['alert_id'], severity=notification_data['severity'])
        
        # Send to all configured channels
        await asyncio.gather(
            self.send_to_webhook(notification_data),
            self.send_to_console(notification_data),
            return_exceptions=True
        )
    
    async def send_escalation(self, alert):
        """Send escalation notification."""
        # Handle both Alert objects and dict objects
        if isinstance(alert, dict):
            notification_data = {
                'alert_id': alert['id'],
                'pattern_name': alert['pattern_name'],
                'severity': alert['severity'],
                'message': f"ESCALATED: {alert['message']}",
                'count': alert['count'],
                'timestamp': alert['last_occurrence'],
                'state': alert['state'],
                'escalated': True
            }
        else:
            notification_data = {
                'alert_id': alert.id,
                'pattern_name': alert.pattern_name,
                'severity': alert.severity,
                'message': f"ESCALATED: {alert.message}",
                'count': alert.count,
                'timestamp': alert.last_occurrence.isoformat(),
                'state': alert.state,
                'escalated': True
            }
        
        logger.warning("Sending escalation notification", alert_id=notification_data['alert_id'])
        
        await asyncio.gather(
            self.send_to_webhook(notification_data),
            self.send_to_console(notification_data),
            return_exceptions=True
        )
    
    async def send_to_webhook(self, data: Dict):
        """Send notification via webhook."""
        if not settings.SLACK_WEBHOOK_URL:
            return
        
        try:
            payload = {
                "text": f"🚨 Alert: {data['pattern_name']} ({data['severity']})",
                "attachments": [{
                    "color": self.get_color_for_severity(data['severity']),
                    "fields": [
                        {"title": "Pattern", "value": data['pattern_name'], "short": True},
                        {"title": "Severity", "value": data['severity'], "short": True},
                        {"title": "Count", "value": str(data['count']), "short": True},
                        {"title": "State", "value": data['state'], "short": True},
                        {"title": "Message", "value": data['message'], "short": False}
                    ],
                    "timestamp": data['timestamp']
                }]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.SLACK_WEBHOOK_URL,
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                
        except Exception as e:
            logger.error("Failed to send webhook notification", error=str(e))
    
    async def send_to_console(self, data: Dict):
        """Send notification to console (for demo purposes)."""
        severity_emoji = {
            'low': '🟢',
            'medium': '🟡', 
            'high': '🟠',
            'critical': '🔴'
        }
        
        emoji = severity_emoji.get(data['severity'], '⚪')
        escalated = " [ESCALATED]" if data.get('escalated') else ""
        
        print(f"\n{emoji} ALERT{escalated}: {data['pattern_name']} ({data['severity']})")
        print(f"   Message: {data['message']}")
        print(f"   Count: {data['count']} | State: {data['state']}")
        print(f"   Time: {data['timestamp']}")
        print("-" * 60)
    
    def get_color_for_severity(self, severity: str) -> str:
        """Get color code for severity level."""
        colors = {
            'low': 'good',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'danger'
        }
        return colors.get(severity, 'warning')
    
    async def acknowledge_alert(self, alert_id: int, acknowledged_by: str):
        """Mark alert as acknowledged."""
        from config.database import get_db
        
        db = next(get_db())
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.state = 'ACKNOWLEDGED'
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.utcnow()
                db.commit()
                
                logger.info("Alert acknowledged", 
                          alert_id=alert_id, 
                          acknowledged_by=acknowledged_by)
        finally:
            db.close()
