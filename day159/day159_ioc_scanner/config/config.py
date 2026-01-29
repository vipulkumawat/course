from dataclasses import dataclass
from typing import List, Dict

@dataclass
class IOCConfig:
    """Configuration for IOC scanning system"""
    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Database configuration
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ioc_scanner"
    db_user: str = "postgres"
    db_password: str = "postgres"
    
    # Scanner configuration
    max_workers: int = 4
    batch_size: int = 100
    cache_ttl: int = 3600  # 1 hour
    
    # Threat feed URLs
    threat_feeds: List[str] = None
    
    # Alert thresholds
    severity_thresholds: Dict[str, int] = None
    
    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    def __post_init__(self):
        if self.threat_feeds is None:
            self.threat_feeds = [
                "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
                "https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/firehol_level1.netset"
            ]
        
        if self.severity_thresholds is None:
            self.severity_thresholds = {
                "CRITICAL": 90,
                "HIGH": 70,
                "MEDIUM": 50,
                "LOW": 30,
                "INFO": 0
            }

config = IOCConfig()
