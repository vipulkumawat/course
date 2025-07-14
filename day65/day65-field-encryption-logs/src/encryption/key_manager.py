import json
import redis
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from src.encryption.encryption_engine import EncryptionKey
import logging

class KeyManager:
    """Manages encryption keys with Redis persistence and rotation."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.logger = logging.getLogger(__name__)
        self.redis_client = redis.from_url(redis_url)
        self.key_prefix = "encryption:keys:"
        
    def store_key(self, key: EncryptionKey) -> bool:
        """Store encryption key in Redis."""
        try:
            key_data = {
                'key_id': key.key_id,
                'key_value': key.key_value.hex(),  # Store as hex string
                'created_at': key.created_at.isoformat(),
                'expires_at': key.expires_at.isoformat(),
                'algorithm': key.algorithm
            }
            
            redis_key = f"{self.key_prefix}{key.key_id}"
            self.redis_client.setex(
                redis_key,
                timedelta(days=35),  # Store 5 days longer than expiry
                json.dumps(key_data)
            )
            
            # Track in key list
            self.redis_client.sadd("encryption:key_list", key.key_id)
            
            self.logger.info(f"Stored key {key.key_id} in Redis")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store key {key.key_id}: {e}")
            return False
    
    def retrieve_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Retrieve encryption key from Redis."""
        try:
            redis_key = f"{self.key_prefix}{key_id}"
            key_data_json = self.redis_client.get(redis_key)
            
            if not key_data_json:
                return None
                
            key_data = json.loads(key_data_json)
            
            return EncryptionKey(
                key_id=key_data['key_id'],
                key_value=bytes.fromhex(key_data['key_value']),
                created_at=datetime.fromisoformat(key_data['created_at']),
                expires_at=datetime.fromisoformat(key_data['expires_at']),
                algorithm=key_data['algorithm']
            )
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve key {key_id}: {e}")
            return None
    
    def list_keys(self) -> List[str]:
        """List all stored key IDs."""
        try:
            key_ids = self.redis_client.smembers("encryption:key_list")
            return [key_id.decode('utf-8') for key_id in key_ids]
        except Exception as e:
            self.logger.error(f"Failed to list keys: {e}")
            return []
    
    def cleanup_expired_keys(self) -> int:
        """Remove expired keys from storage."""
        cleaned_count = 0
        
        for key_id in self.list_keys():
            key = self.retrieve_key(key_id)
            if key and key.is_expired():
                try:
                    redis_key = f"{self.key_prefix}{key_id}"
                    self.redis_client.delete(redis_key)
                    self.redis_client.srem("encryption:key_list", key_id)
                    cleaned_count += 1
                    self.logger.info(f"Cleaned expired key {key_id}")
                except Exception as e:
                    self.logger.error(f"Failed to clean key {key_id}: {e}")
        
        return cleaned_count
    
    def get_stats(self) -> Dict[str, any]:
        """Get key management statistics."""
        key_list = self.list_keys()
        expired_count = 0
        
        for key_id in key_list:
            key = self.retrieve_key(key_id)
            if key and key.is_expired():
                expired_count += 1
        
        return {
            'total_keys': len(key_list),
            'expired_keys': expired_count,
            'active_keys': len(key_list) - expired_count,
            'redis_connection': self.redis_client.ping()
        }
