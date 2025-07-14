import json
import redis
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

class MetadataHandler:
    """Handles encryption metadata storage and retrieval."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.logger = logging.getLogger(__name__)
        self.redis_client = redis.from_url(redis_url)
        self.metadata_prefix = "log:metadata:"
        self.audit_prefix = "audit:encryption:"
        
    async def store_log_metadata(self, log_id: str, metadata: Dict[str, Any]) -> bool:
        """Store log encryption metadata."""
        try:
            metadata_key = f"{self.metadata_prefix}{log_id}"
            
            # Store metadata with 30-day TTL
            self.redis_client.setex(
                metadata_key,
                timedelta(days=30),
                json.dumps(metadata)
            )
            
            # Create audit entry
            await self._create_audit_entry(log_id, metadata)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store metadata for log {log_id}: {e}")
            return False
    
    async def retrieve_log_metadata(self, log_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve log encryption metadata."""
        try:
            metadata_key = f"{self.metadata_prefix}{log_id}"
            metadata_json = self.redis_client.get(metadata_key)
            
            if metadata_json:
                return json.loads(metadata_json)
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve metadata for log {log_id}: {e}")
            return None
    
    async def _create_audit_entry(self, log_id: str, metadata: Dict[str, Any]):
        """Create audit trail entry for encryption operations."""
        try:
            audit_entry = {
                'log_id': log_id,
                'timestamp': datetime.utcnow().isoformat(),
                'encrypted_fields_count': len(metadata.get('encrypted_fields', [])),
                'encryption_keys_used': [
                    field['key_id'] for field in metadata.get('encrypted_fields', [])
                ],
                'processor_version': metadata.get('processor_version', 'unknown')
            }
            
            audit_key = f"{self.audit_prefix}{datetime.utcnow().strftime('%Y%m%d')}:{log_id}"
            
            # Store audit entry with 90-day retention
            self.redis_client.setex(
                audit_key,
                timedelta(days=90),
                json.dumps(audit_entry)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create audit entry for log {log_id}: {e}")
    
    def get_audit_stats(self, date: str = None) -> Dict[str, Any]:
        """Get audit statistics for a specific date."""
        if not date:
            date = datetime.utcnow().strftime('%Y%m%d')
        
        try:
            pattern = f"{self.audit_prefix}{date}:*"
            audit_keys = self.redis_client.keys(pattern)
            
            total_logs = len(audit_keys)
            total_encrypted_fields = 0
            unique_keys = set()
            
            for key in audit_keys:
                audit_data = json.loads(self.redis_client.get(key))
                total_encrypted_fields += audit_data.get('encrypted_fields_count', 0)
                unique_keys.update(audit_data.get('encryption_keys_used', []))
            
            return {
                'date': date,
                'total_logs_processed': total_logs,
                'total_fields_encrypted': total_encrypted_fields,
                'unique_encryption_keys': len(unique_keys),
                'average_fields_per_log': total_encrypted_fields / max(total_logs, 1)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get audit stats for {date}: {e}")
            return {}
