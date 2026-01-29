"""Parse security logs and extract raw events"""
import json
from datetime import datetime
from typing import Dict, Any, List
import re

class LogParser:
    """Parse authentication and access logs"""
    
    def __init__(self):
        self.event_types = {
            'login': r'user\s+(\w+)\s+logged\s+in',
            'access': r'user\s+(\w+)\s+accessed\s+(\S+)',
            'download': r'user\s+(\w+)\s+downloaded\s+(\d+)\s+bytes',
            'failed_login': r'failed\s+login\s+for\s+user\s+(\w+)'
        }
    
    def parse(self, log_entry: str) -> Dict[str, Any]:
        """Parse a single log entry"""
        timestamp = datetime.now()
        user = None
        event_type = 'unknown'
        details = {}
        
        # Try to match known patterns
        for evt_type, pattern in self.event_types.items():
            match = re.search(pattern, log_entry, re.IGNORECASE)
            if match:
                event_type = evt_type
                user = match.group(1)
                
                if evt_type == 'access':
                    details['resource'] = match.group(2)
                elif evt_type == 'download':
                    details['bytes'] = int(match.group(2))
                
                break
        
        return {
            'timestamp': timestamp.isoformat(),
            'user': user,
            'event_type': event_type,
            'details': details,
            'raw': log_entry
        }
    
    def parse_structured(self, log_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Parse structured log entry"""
        return {
            'timestamp': log_dict.get('timestamp', datetime.now().isoformat()),
            'user': log_dict.get('user'),
            'event_type': log_dict.get('event_type', 'unknown'),
            'details': log_dict.get('details', {}),
            'ip_address': log_dict.get('ip_address'),
            'session_id': log_dict.get('session_id')
        }
