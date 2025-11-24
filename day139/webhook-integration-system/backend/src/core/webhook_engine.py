import sys
import os
# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
import json
import hashlib
import hmac
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from sqlalchemy.orm import Session

from src.models.webhook import WebhookEndpoint, WebhookDelivery
from src.utils.template_engine import TemplateEngine

logger = structlog.get_logger()

class WebhookEngine:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.template_engine = TemplateEngine()
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def process_event(self, event_data: Dict) -> List[str]:
        """Process incoming event and trigger matching webhooks"""
        delivery_ids = []
        
        # Find matching webhook endpoints
        endpoints = self.db_session.query(WebhookEndpoint).filter(
            WebhookEndpoint.is_active == True
        ).all()
        
        for endpoint in endpoints:
            if self._matches_filters(event_data, endpoint.event_filters):
                delivery_id = await self._create_delivery(endpoint, event_data)
                delivery_ids.append(delivery_id)
                
                # Schedule immediate delivery attempt
                asyncio.create_task(self._deliver_webhook(delivery_id))
        
        return delivery_ids
    
    def _matches_filters(self, event_data: Dict, filters: List[Dict]) -> bool:
        """Check if event matches endpoint filters"""
        if not filters:
            return True
            
        for filter_rule in filters:
            field = filter_rule.get('field')
            operator = filter_rule.get('operator', 'equals')
            value = filter_rule.get('value')
            
            event_value = self._get_nested_field(event_data, field)
            
            if operator == 'equals' and event_value == value:
                return True
            elif operator == 'contains' and value in str(event_value):
                return True
            elif operator == 'greater_than' and float(event_value) > float(value):
                return True
            elif operator == 'regex':
                import re
                if re.match(value, str(event_value)):
                    return True
                    
        return False
    
    def _get_nested_field(self, data: Dict, field_path: str):
        """Extract nested field value using dot notation"""
        keys = field_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    async def _create_delivery(self, endpoint: WebhookEndpoint, event_data: Dict) -> str:
        """Create delivery record and prepare payload"""
        # Transform payload using template
        payload = self.template_engine.transform(
            event_data, 
            endpoint.payload_template
        )
        
        delivery = WebhookDelivery(
            endpoint_id=endpoint.id,
            event_data=event_data,
            payload=json.dumps(payload),
            status="pending",
            max_attempts=3
        )
        
        self.db_session.add(delivery)
        self.db_session.commit()
        
        logger.info("Webhook delivery created", 
                   endpoint_name=endpoint.name, 
                   delivery_id=delivery.id)
        
        return delivery.id
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2))
    async def _deliver_webhook(self, delivery_id: str):
        """Deliver webhook with retry logic"""
        delivery = self.db_session.query(WebhookDelivery).filter(
            WebhookDelivery.id == delivery_id
        ).first()
        
        if not delivery:
            logger.error("Delivery not found", delivery_id=delivery_id)
            return
            
        endpoint = self.db_session.query(WebhookEndpoint).filter(
            WebhookEndpoint.id == delivery.endpoint_id
        ).first()
        
        if not endpoint:
            logger.error("Endpoint not found", endpoint_id=delivery.endpoint_id)
            return
        
        try:
            delivery.attempt_count += 1
            delivery.status = "delivering"
            self.db_session.commit()
            
            # Prepare request
            headers = {"Content-Type": "application/json"}
            payload_data = json.loads(delivery.payload)
            
            # Add authentication
            self._add_authentication(headers, payload_data, endpoint)
            
            # Send request
            response = await self.client.request(
                method=endpoint.method,
                url=endpoint.url,
                json=payload_data,
                headers=headers
            )
            
            # Update delivery status
            delivery.status = "delivered" if response.is_success else "failed"
            delivery.response_code = response.status_code
            delivery.response_body = response.text[:1000]  # Truncate response
            
            if response.is_success:
                delivery.delivered_at = datetime.utcnow()
                logger.info("Webhook delivered successfully", 
                           delivery_id=delivery_id,
                           status_code=response.status_code)
            else:
                logger.warning("Webhook delivery failed", 
                              delivery_id=delivery_id,
                              status_code=response.status_code)
                
        except Exception as e:
            delivery.status = "failed"
            delivery.response_body = str(e)[:500]
            logger.error("Webhook delivery exception", 
                        delivery_id=delivery_id, 
                        error=str(e))
            
            # Schedule retry if attempts remaining
            if delivery.attempt_count < delivery.max_attempts:
                delivery.status = "retrying"
                retry_delay = 2 ** delivery.attempt_count  # Exponential backoff
                delivery.next_retry = datetime.utcnow() + timedelta(seconds=retry_delay)
                
        finally:
            delivery.updated_at = datetime.utcnow()
            self.db_session.commit()
    
    def _add_authentication(self, headers: Dict, payload: Dict, endpoint: WebhookEndpoint):
        """Add authentication to webhook request"""
        auth_config = endpoint.auth_config or {}
        
        if endpoint.auth_type == "bearer":
            token = auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
                
        elif endpoint.auth_type == "api_key":
            key = auth_config.get("key")
            header_name = auth_config.get("header", "X-API-Key")
            if key:
                headers[header_name] = key
                
        elif endpoint.auth_type == "hmac":
            secret = auth_config.get("secret")
            if secret:
                payload_str = json.dumps(payload, separators=(',', ':'))
                signature = hmac.new(
                    secret.encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"
