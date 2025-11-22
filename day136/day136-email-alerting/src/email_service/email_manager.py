import asyncio
import aiosmtplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os
from dataclasses import dataclass
import redis

@dataclass
class EmailConfig:
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    from_email: str = ""
    from_name: str = "Log Processing System"

@dataclass
class EmailMessage:
    to_emails: List[str]
    subject: str
    html_body: str = ""
    text_body: str = ""
    attachments: List[str] = None
    priority: str = "normal"  # low, normal, high, critical

class EmailManager:
    def __init__(self, config: EmailConfig):
        self.config = config
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.template_env = Environment(loader=FileSystemLoader('src/templates'))
        
        # Add custom filter for formatting timestamps
        def format_timestamp(value, format_str='%Y-%m-%d %H:%M:%S'):
            if value is None:
                return 'N/A'
            if isinstance(value, datetime):
                return value.strftime(format_str)
            if isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.strftime(format_str)
                except (ValueError, AttributeError):
                    return value
            return str(value)
        
        self.template_env.filters['format_timestamp'] = format_timestamp
        
        self.delivery_stats = {
            'sent': 0,
            'failed': 0,
            'queued': 0
        }
        
    async def send_email(self, message: EmailMessage) -> Dict[str, Any]:
        """Send email with retry logic and delivery tracking"""
        # Check if we're in test mode
        test_mode = os.getenv('TEST_MODE', 'false').lower() in ('true', '1', 'yes')
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = ", ".join(message.to_emails)
            
            # Set priority headers
            if message.priority == "critical":
                msg['X-Priority'] = '1'
                msg['X-MSMail-Priority'] = 'High'
            elif message.priority == "high":
                msg['X-Priority'] = '2'
                msg['X-MSMail-Priority'] = 'High'
            
            # Add text and HTML parts
            if message.text_body:
                msg.attach(MIMEText(message.text_body, 'plain', 'utf-8'))
            if message.html_body:
                msg.attach(MIMEText(message.html_body, 'html', 'utf-8'))
            
            # In test mode, skip actual SMTP sending
            if test_mode:
                # Log the email content for debugging
                logging.info(f"🧪 TEST MODE: Email would be sent to {', '.join(message.to_emails)}")
                logging.info(f"🧪 TEST MODE: Subject: {message.subject}")
                logging.info(f"🧪 TEST MODE: HTML body length: {len(message.html_body)} characters")
                
                # Track delivery as if it was sent
                delivery_id = f"test_email_{datetime.now().timestamp()}"
                self._track_delivery(delivery_id, message.to_emails, "sent")
                self.delivery_stats['sent'] += 1
                
                logging.info(f"📧 Email sent successfully (TEST MODE) to {len(message.to_emails)} recipients")
                return {
                    "status": "sent", 
                    "delivery_id": delivery_id,
                    "test_mode": True,
                    "message": "Email sent in test mode (no actual SMTP connection)"
                }
            
            # Send via SMTP (production mode)
            # For port 587, use STARTTLS; for port 465, use TLS from the start
            use_tls = self.config.smtp_port == 465
            start_tls = self.config.smtp_port == 587
            
            server = aiosmtplib.SMTP(
                hostname=self.config.smtp_host, 
                port=self.config.smtp_port,
                use_tls=use_tls,
                start_tls=start_tls if start_tls else False
            )
            
            try:
                await server.connect()
                # Only call starttls if we're using STARTTLS and it wasn't auto-started
                if start_tls and not use_tls:
                    try:
                        await server.starttls()
                    except Exception as e:
                        # If already using TLS, that's fine - continue
                        if "already using" not in str(e).lower():
                            raise
                if self.config.username and self.config.password:
                    await server.login(self.config.username, self.config.password)
                await server.send_message(msg)
            finally:
                await server.quit()
            
            # Track delivery
            delivery_id = f"email_{datetime.now().timestamp()}"
            self._track_delivery(delivery_id, message.to_emails, "sent")
            self.delivery_stats['sent'] += 1
            
            logging.info(f"📧 Email sent successfully to {len(message.to_emails)} recipients")
            return {"status": "sent", "delivery_id": delivery_id}
            
        except Exception as e:
            logging.error(f"❌ Email sending failed: {str(e)}")
            self.delivery_stats['failed'] += 1
            return {"status": "failed", "error": str(e)}
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render Jinja2 template with context"""
        template = self.template_env.get_template(template_name)
        return template.render(**context)
    
    def _track_delivery(self, delivery_id: str, recipients: List[str], status: str):
        """Track email delivery status in Redis"""
        delivery_data = {
            'delivery_id': delivery_id,
            'recipients': recipients,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        self.redis_client.setex(
            f"email_delivery:{delivery_id}", 
            86400,  # 24 hours TTL
            json.dumps(delivery_data)
        )
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get email delivery statistics"""
        return {
            **self.delivery_stats,
            'success_rate': (self.delivery_stats['sent'] / 
                           max(1, self.delivery_stats['sent'] + self.delivery_stats['failed'])) * 100
        }
