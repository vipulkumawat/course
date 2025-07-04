"""
Configuration for distributed query engine
"""
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class QueryConfig:
    """Configuration for query engine"""
    
    # Parser settings
    max_query_length: int = 10000
    supported_functions: List[str] = None
    
    # Planner settings
    enable_partition_pruning: bool = True
    enable_predicate_pushdown: bool = True
    enable_aggregation_distribution: bool = True
    max_parallelism: int = 10
    
    # Executor settings
    default_timeout_seconds: int = 30
    max_concurrent_queries: int = 100
    retry_attempts: int = 3
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = None
    
    def __post_init__(self):
        if self.supported_functions is None:
            self.supported_functions = ["COUNT", "SUM", "AVG", "MIN", "MAX"]
        
        if self.cors_origins is None:
            self.cors_origins = ["*"]

# Default configuration
default_config = QueryConfig()
