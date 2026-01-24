"""
Security Event Normalizer - Transform raw logs into standardized security events
"""
import json
import time
import hashlib
from typing import Dict, Optional
from datetime import datetime
import structlog

from src.siem.engine import SecurityEvent, EventType

logger = structlog.get_logger()


class EventNormalizer:
    """Normalize various log formats into security events"""
    
    def __init__(self):
        self.event_count = 0
    
    def normalize_auth_log(self, raw_log: Dict) -> Optional[SecurityEvent]:
        """Normalize authentication logs"""
        try:
            event_id = self._generate_event_id(raw_log)
            
            # Determine event type
            event_type = EventType.AUTH_SUCCESS if raw_log.get('success', False) else EventType.AUTH_FAILURE
            
            return SecurityEvent(
                event_id=event_id,
                timestamp=raw_log.get('timestamp', time.time()),
                event_type=event_type,
                user=raw_log.get('username', 'unknown'),
                source_ip=raw_log.get('source_ip', '0.0.0.0'),
                destination=raw_log.get('destination', None),
                action='authentication',
                success=raw_log.get('success', False),
                metadata={
                    'method': raw_log.get('auth_method', 'password'),
                    'user_agent': raw_log.get('user_agent', ''),
                    'geo_location': raw_log.get('geo_location', {}),
                    'service': raw_log.get('service', 'unknown')
                }
            )
        except Exception as e:
            logger.error("Failed to normalize auth log", error=str(e))
            return None
    
    def normalize_access_log(self, raw_log: Dict) -> Optional[SecurityEvent]:
        """Normalize file/data access logs"""
        try:
            event_id = self._generate_event_id(raw_log)
            
            return SecurityEvent(
                event_id=event_id,
                timestamp=raw_log.get('timestamp', time.time()),
                event_type=EventType.DATA_ACCESS,
                user=raw_log.get('user', 'unknown'),
                source_ip=raw_log.get('client_ip', '0.0.0.0'),
                destination=raw_log.get('resource_path', None),
                action=raw_log.get('action', 'read'),
                success=raw_log.get('status_code', 200) < 400,
                metadata={
                    'resource': raw_log.get('resource_path', ''),
                    'resource_type': raw_log.get('resource_type', 'file'),
                    'bytes_transferred': raw_log.get('bytes', 0),
                    'critical_asset': self._is_critical_asset(raw_log)
                }
            )
        except Exception as e:
            logger.error("Failed to normalize access log", error=str(e))
            return None
    
    def normalize_admin_log(self, raw_log: Dict) -> Optional[SecurityEvent]:
        """Normalize administrative action logs"""
        try:
            event_id = self._generate_event_id(raw_log)
            
            # Check if this is privilege escalation
            action = raw_log.get('action', '').lower()
            is_priv_escalation = any(
                keyword in action 
                for keyword in ['sudo', 'su', 'admin', 'privilege', 'elevate']
            )
            
            event_type = EventType.PRIVILEGE_ESCALATION if is_priv_escalation else EventType.ADMIN_ACTION
            
            return SecurityEvent(
                event_id=event_id,
                timestamp=raw_log.get('timestamp', time.time()),
                event_type=event_type,
                user=raw_log.get('user', 'unknown'),
                source_ip=raw_log.get('source_ip', '0.0.0.0'),
                destination=raw_log.get('target', None),
                action=action,
                success=raw_log.get('success', True),
                metadata={
                    'command': raw_log.get('command', ''),
                    'target_user': raw_log.get('target_user', ''),
                    'session_id': raw_log.get('session_id', '')
                }
            )
        except Exception as e:
            logger.error("Failed to normalize admin log", error=str(e))
            return None
    
    def _generate_event_id(self, raw_log: Dict) -> str:
        """Generate unique event ID"""
        self.event_count += 1
        content = json.dumps(raw_log, sort_keys=True)
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"EVT-{int(time.time())}-{hash_val}-{self.event_count}"
    
    def _is_critical_asset(self, raw_log: Dict) -> bool:
        """Determine if accessed resource is a critical asset"""
        resource = raw_log.get('resource_path', '').lower()
        critical_patterns = ['admin', 'database', 'payment', 'credential', 'secret', 'private']
        return any(pattern in resource for pattern in critical_patterns)
