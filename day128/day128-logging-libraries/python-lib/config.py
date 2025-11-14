import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class LogConfig:
    """Configuration for distributed logging client"""
    
    # Server configuration
    endpoint: str = "http://localhost:8080/api/logs"
    api_key: Optional[str] = None
    
    # Application identification
    service_name: str = "unknown-service"
    component_name: str = "main"
    environment: str = "development"
    
    # Batching configuration
    batch_size: int = 100
    batch_timeout_ms: int = 5000
    
    # Network configuration
    connection_timeout_s: int = 5
    retry_attempts: int = 3
    retry_backoff_base: float = 1.0
    
    # Buffer configuration
    max_buffer_size: int = 10000
    enable_local_buffer: bool = True
    buffer_file_path: str = "/tmp/distributed_logs.buffer"
    
    # Performance
    async_enabled: bool = True
    thread_pool_size: int = 4
    
    @classmethod
    def from_env(cls) -> 'LogConfig':
        """Create configuration from environment variables"""
        return cls(
            endpoint=os.getenv('LOG_ENDPOINT', 'http://localhost:8080/api/logs'),
            api_key=os.getenv('LOG_API_KEY'),
            service_name=os.getenv('SERVICE_NAME', 'unknown-service'),
            component_name=os.getenv('COMPONENT_NAME', 'main'),
            environment=os.getenv('ENVIRONMENT', 'development'),
            batch_size=int(os.getenv('LOG_BATCH_SIZE', '100')),
            batch_timeout_ms=int(os.getenv('LOG_BATCH_TIMEOUT_MS', '5000')),
            async_enabled=os.getenv('LOG_ASYNC_ENABLED', 'true').lower() == 'true'
        )
