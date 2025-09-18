import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from enum import Enum

class TierType(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    ARCHIVE = "archive"

class PolicyEngine:
    def __init__(self, config: Dict):
        self.config = config
        self.access_patterns = {}  # Track access patterns
    
    async def should_migrate(self, log_data: Dict, from_tier: TierType, to_tier: TierType) -> bool:
        """Determine if data should be migrated based on policies"""
        
        # Age-based policy
        stored_at = datetime.fromisoformat(log_data.get("stored_at", datetime.now().isoformat()))
        age_days = (datetime.now() - stored_at).days
        
        # Check age thresholds
        if from_tier == TierType.HOT and to_tier == TierType.WARM:
            return age_days >= self.config.get("HOT_TO_WARM_DAYS", 7)
        elif from_tier == TierType.WARM and to_tier == TierType.COLD:
            return age_days >= self.config.get("WARM_TO_COLD_DAYS", 30)
        elif from_tier == TierType.COLD and to_tier == TierType.ARCHIVE:
            return age_days >= self.config.get("COLD_TO_ARCHIVE_DAYS", 365)
        
        # Access pattern policy
        entry_id = log_data.get("entry_id", "")
        access_count = self.access_patterns.get(entry_id, 0)
        
        # Don't migrate frequently accessed data
        if access_count > 10 and age_days < 30:
            return False
        
        # Priority-based policy
        priority = log_data.get("priority", "normal")
        if priority == "high" and age_days < 14:
            return False
        
        return True
    
    def record_access(self, entry_id: str):
        """Record access to an entry for pattern analysis"""
        self.access_patterns[entry_id] = self.access_patterns.get(entry_id, 0) + 1
    
    def get_migration_policies(self) -> Dict:
        """Get current migration policies"""
        return {
            "hot_to_warm_days": self.config.get("HOT_TO_WARM_DAYS", 7),
            "warm_to_cold_days": self.config.get("WARM_TO_COLD_DAYS", 30),
            "cold_to_archive_days": self.config.get("COLD_TO_ARCHIVE_DAYS", 365),
            "access_threshold": 10,
            "high_priority_retention_days": 14
        }
