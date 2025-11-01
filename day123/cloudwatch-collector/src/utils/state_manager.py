"""State management for log stream positions."""
import redis
import json
import logging
from typing import Optional, Dict, Any
import os


logger = logging.getLogger(__name__)


class StateManager:
    """Manages log stream processing state."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize state manager."""
        self.config = config
        self.storage_type = config['collector']['state']['storage_type']
        
        if self.storage_type == 'redis':
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True
            )
            logger.info("Using Redis for state management")
        else:
            self.file_path = 'data/checkpoints/state.json'
            self._ensure_file()
            logger.info(f"Using file storage for state management: {self.file_path}")
    
    def _ensure_file(self):
        """Ensure checkpoint file exists."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({}, f)
    
    def get_position(self, key: str) -> Optional[str]:
        """Get last processed position for a stream."""
        try:
            if self.storage_type == 'redis':
                return self.redis_client.get(f"position:{key}")
            else:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    return data.get(key)
        except Exception as e:
            logger.error(f"Failed to get position for {key}: {e}")
            return None
    
    def update_position(self, key: str, token: str):
        """Update last processed position for a stream."""
        try:
            if self.storage_type == 'redis':
                self.redis_client.set(f"position:{key}", token)
            else:
                with open(self.file_path, 'r+') as f:
                    data = json.load(f)
                    data[key] = token
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
        except Exception as e:
            logger.error(f"Failed to update position for {key}: {e}")
    
    def clear_position(self, key: str):
        """Clear position for a stream."""
        try:
            if self.storage_type == 'redis':
                self.redis_client.delete(f"position:{key}")
            else:
                with open(self.file_path, 'r+') as f:
                    data = json.load(f)
                    if key in data:
                        del data[key]
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
        except Exception as e:
            logger.error(f"Failed to clear position for {key}: {e}")
