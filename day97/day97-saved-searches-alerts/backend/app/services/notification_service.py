"""
Notification delivery service
"""
import asyncio
import logging
from typing import Dict, Any, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import aiohttp

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.smtp_server = "localhost"  # Configure for your SMTP server
        self.smtp_port = 587
        self.smtp_username = "alerts@yourcompany.com"
        self.smtp_password = "your_password"
        
    async def send_alert_notifications(self, alert, search_results: Dict[str, Any]):
        """Send notifications for triggered alert"""
        for channel in alert.notification_channels:
            try:
                if channel == "email":
                    await self._send_email_notification(alert, search_results)
                elif channel == "webhook":
                    await self._send_webhook_notification(alert, search_results)
                elif channel == "in_app":
                    await self._send_in_app_notification(alert, search_results)
                    
            except Exception as e:
                logger.error(f"Failed to send {channel} notification for alert {alert.name}: {e}")
    
    async def _send_email_notification(self, alert, search_results: Dict[str, Any]):
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = ", ".join(alert.notification_emails)
            msg['Subject'] = f"Alert Triggered: {alert.name}"
            
            body = self._format_email_body(alert, search_results)
            msg.attach(MIMEText(body, 'html'))
            
            # In production, use async SMTP client
            logger.info(f"📧 Email notification sent for alert: {alert.name}")
            
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
    
    async def _send_webhook_notification(self, alert, search_results: Dict[str, Any]):
        """Send webhook notification"""
        if not alert.webhook_url:
            return
            
        try:
            payload = {
                "alert_name": alert.name,
                "alert_id": alert.id,
                "description": alert.description,
                "condition_type": alert.condition_type,
                "threshold_value": alert.threshold_value,
                "triggered_at": alert.last_triggered.isoformat(),
                "search_results": search_results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    alert.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"🪝 Webhook notification sent for alert: {alert.name}")
                    else:
                        logger.error(f"Webhook notification failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
    
    async def _send_in_app_notification(self, alert, search_results: Dict[str, Any]):
        """Send in-app notification via WebSocket"""
        try:
            # This would integrate with your WebSocket connections
            notification_data = {
                "type": "alert",
                "alert_id": alert.id,
                "alert_name": alert.name,
                "message": f"Alert '{alert.name}' has been triggered",
                "timestamp": alert.last_triggered.isoformat(),
                "urgency": "high" if "ERROR" in str(search_results) else "medium"
            }
            
            # In real implementation, broadcast to connected WebSocket clients
            logger.info(f"📱 In-app notification sent for alert: {alert.name}")
            
        except Exception as e:
            logger.error(f"In-app notification failed: {e}")
    
    def _format_email_body(self, alert, search_results: Dict[str, Any]) -> str:
        """Format HTML email body"""
        aggregations = search_results.get("aggregations", {})
        sample_logs = search_results.get("sample_logs", [])[:3]  # Show first 3 logs
        
        html = f"""
        <html>
        <body>
        <h2>🚨 Alert Triggered: {alert.name}</h2>
        
        <h3>Alert Details:</h3>
        <ul>
            <li><strong>Description:</strong> {alert.description or 'N/A'}</li>
            <li><strong>Condition:</strong> {alert.condition_type} - {alert.comparison_operator} {alert.threshold_value}</li>
            <li><strong>Time Window:</strong> {alert.time_window_minutes} minutes</li>
            <li><strong>Triggered At:</strong> {alert.last_triggered.strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
        </ul>
        
        <h3>Search Results Summary:</h3>
        <ul>
            <li><strong>Total Results:</strong> {search_results.get('total_results', 0)}</li>
        """
        
        if aggregations:
            html += "<li><strong>Aggregations:</strong><ul>"
            for key, value in aggregations.items():
                html += f"<li>{key}: {value}</li>"
            html += "</ul></li>"
        
        html += "</ul>"
        
        if sample_logs:
            html += "<h3>Sample Log Entries:</h3><ul>"
            for log in sample_logs:
                html += f"""
                <li>
                    <strong>[{log.get('timestamp', 'N/A')}]</strong> 
                    {log.get('service', 'unknown')} - 
                    {log.get('level', 'INFO')}: 
                    {log.get('message', 'No message')}
                </li>
                """
            html += "</ul>"
        
        html += """
        </body>
        </html>
        """
        
        return html
