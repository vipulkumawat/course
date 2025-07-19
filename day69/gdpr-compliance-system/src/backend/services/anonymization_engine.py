import hashlib
import secrets
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()

class AnonymizationEngine:
    def __init__(self):
        self.salt = secrets.token_hex(32)
    
    def anonymize_user_id(self, user_id: str) -> str:
        """Convert user ID to anonymous hash"""
        return hashlib.sha256(f"{user_id}{self.salt}".encode()).hexdigest()[:16]
    
    def anonymize_ip_address(self, ip_address: str) -> str:
        """Anonymize IP address by zeroing last octet"""
        if '.' in ip_address:  # IPv4
            parts = ip_address.split('.')
            return '.'.join(parts[:3] + ['0'])
        else:  # IPv6 or invalid
            return "0000:0000:0000:0000:0000:0000:0000:0000"
    
    def anonymize_email(self, email: str) -> str:
        """Anonymize email address"""
        return f"anonymous{self.anonymize_user_id(email)[:8]}@example.com"
    
    def should_anonymize(self, data_type: str) -> bool:
        """Determine if data should be anonymized vs deleted"""
        anonymizable_types = {
            'analytics_events',
            'performance_metrics',
            'system_logs',
            'aggregated_data'
        }
        
        return data_type in anonymizable_types
    
    def anonymize_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize a complete log entry"""
        anonymized = log_entry.copy()
        
        # Anonymize common PII fields
        if 'user_id' in anonymized:
            anonymized['user_id'] = self.anonymize_user_id(anonymized['user_id'])
        
        if 'ip_address' in anonymized:
            anonymized['ip_address'] = self.anonymize_ip_address(anonymized['ip_address'])
        
        if 'email' in anonymized:
            anonymized['email'] = self.anonymize_email(anonymized['email'])
        
        # Remove direct identifiers
        for field in ['name', 'phone', 'address', 'ssn']:
            if field in anonymized:
                del anonymized[field]
        
        logger.info("Log entry anonymized", 
                   original_fields=len(log_entry),
                   anonymized_fields=len(anonymized))
        
        return anonymized
