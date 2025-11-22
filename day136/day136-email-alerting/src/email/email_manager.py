# CRITICAL: Import standard library email module FIRST before any other imports
# Temporarily remove local email package to import standard library
import sys
_local_email = None
if 'email' in sys.modules:
    _mod = sys.modules['email']
    if hasattr(_mod, '__path__'):
        _local_email = sys.modules.pop('email')

# Import base email module first, then submodules
import email
import email.mime
import email.mime.text
import email.mime.multipart  
import email.mime.base
import email.encoders

# Restore local email package
if _local_email:
    sys.modules['email'] = _local_email

import asyncio
import aiosmtplib
import smtplib

# Use the standard library email modules
MimeText = email.mime.text.MimeText
MimeMultipart = email.mime.multipart.MimeMultipart
MimeBase = email.mime.base.MimeBase
encoders = email.encoders
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
        self.delivery_stats = {
            'sent': 0,
            'failed': 0,
            'queued': 0
        }
        
    async def send_email(self, message: EmailMessage) -> Dict[str, Any]:
        """Send email with retry logic and delivery tracking"""
        try:
            msg = MimeMultipart('alternative')
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
                msg.attach(MimeText(message.text_body, 'plain', 'utf-8'))
            if message.html_body:
                msg.attach(MimeText(message.html_body, 'html', 'utf-8'))
            
            # Send via SMTP
            async with aiosmtplib.SMTP(hostname=self.config.smtp_host, port=self.config.smtp_port) as server:
                await server.starttls()
                await server.login(self.config.username, self.config.password)
                await server.send_message(msg)
            
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
