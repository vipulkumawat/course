from dataclasses import dataclass
from typing import List, Dict, Any
import os

@dataclass
class EncryptionConfig:
    # AES-256-GCM configuration
    algorithm: str = "AES-256-GCM"
    key_size: int = 32  # 256 bits
    iv_size: int = 12   # 96 bits for GCM
    
    # Key management
    key_rotation_days: int = 30
    key_cache_ttl: int = 3600  # 1 hour
    
    # Field detection patterns
    sensitive_patterns: Dict[str, str] = None
    sensitive_field_names: List[str] = None
    
    # Performance settings
    batch_size: int = 1000
    max_workers: int = 4
    
    def __post_init__(self):
        if self.sensitive_patterns is None:
            self.sensitive_patterns = {
                'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                'ssn': r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
                'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
            }
        
        if self.sensitive_field_names is None:
            self.sensitive_field_names = [
                'email', 'phone', 'telephone', 'ssn', 'social_security',
                'credit_card', 'card_number', 'password', 'secret',
                'token', 'api_key', 'private_key'
            ]

# Global configuration instance
config = EncryptionConfig()

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# RabbitMQ configuration  
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')

# Web interface configuration
WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
WEB_PORT = int(os.getenv('WEB_PORT', '8000'))
