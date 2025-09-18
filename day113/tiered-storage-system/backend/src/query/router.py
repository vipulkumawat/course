import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog
from ..tiers.manager import TierManager, TierType

logger = structlog.get_logger()

class QueryRouter:
    """Routes queries to appropriate storage tiers"""
    
    def __init__(self, tier_manager: TierManager):
        self.tier_manager = tier_manager
        self.query_cache = {}
        self.performance_stats = {
            "hot_queries": 0,
            "warm_queries": 0,
            "cold_queries": 0,
            "archive_queries": 0,
            "cache_hits": 0,
            "total_queries": 0
        }
    
    async def query_log_entry(self, entry_id: str) -> Optional[Dict]:
        """Query a specific log entry across all tiers"""
        self.performance_stats["total_queries"] += 1
        
        # Check cache first
        if entry_id in self.query_cache:
            self.performance_stats["cache_hits"] += 1
            logger.info("Query cache hit", entry_id=entry_id)
            return self.query_cache[entry_id]
        
        # Search through tiers in order of performance
        tier_order = [TierType.HOT, TierType.WARM, TierType.COLD, TierType.ARCHIVE]
        
        for tier in tier_order:
            backend = self.tier_manager.storage_backends[tier]
            
            try:
                data = await backend.read(entry_id)
                if data:
                    log_data = json.loads(data)
                    
                    # Record access for policy engine
                    self.tier_manager.policy_engine.record_access(entry_id)
                    
                    # Update performance stats
                    self.performance_stats[f"{tier.value}_queries"] += 1
                    
                    # Cache result
                    self.query_cache[entry_id] = log_data
                    
                    logger.info("Query successful", 
                               entry_id=entry_id, 
                               tier=tier.value,
                               response_time_simulation=self._get_tier_latency(tier))
                    
                    return log_data
                    
            except Exception as e:
                logger.error("Query error", entry_id=entry_id, tier=tier.value, error=str(e))
                continue
        
        logger.warning("Log entry not found", entry_id=entry_id)
        return None
    
    async def query_by_timerange(self, start_time: datetime, end_time: datetime, 
                                limit: int = 100) -> List[Dict]:
        """Query log entries within a time range"""
        results = []
        
        for tier in [TierType.HOT, TierType.WARM, TierType.COLD, TierType.ARCHIVE]:
            backend = self.tier_manager.storage_backends[tier]
            entries = await backend.list_entries()
            
            for entry_id in entries:
                if len(results) >= limit:
                    break
                
                try:
                    data = await backend.read(entry_id)
                    if data:
                        log_data = json.loads(data)
                        stored_at = datetime.fromisoformat(log_data.get("stored_at", ""))
                        
                        if start_time <= stored_at <= end_time:
                            log_data["queried_from_tier"] = tier.value
                            results.append(log_data)
                            
                except Exception as e:
                    logger.error("Timerange query error", entry_id=entry_id, error=str(e))
        
        # Sort by timestamp
        results.sort(key=lambda x: x.get("stored_at", ""), reverse=True)
        return results[:limit]
    
    async def search_logs(self, query: str, tier_filter: Optional[str] = None) -> List[Dict]:
        """Search logs by content"""
        results = []
        tiers_to_search = [TierType[tier_filter.upper()]] if tier_filter else list(TierType)
        
        for tier in tiers_to_search:
            backend = self.tier_manager.storage_backends[tier]
            entries = await backend.list_entries()
            
            for entry_id in entries:
                try:
                    data = await backend.read(entry_id)
                    if data and query.lower() in data.lower():
                        log_data = json.loads(data)
                        log_data["queried_from_tier"] = tier.value
                        results.append(log_data)
                        
                except Exception as e:
                    logger.error("Search error", entry_id=entry_id, error=str(e))
        
        return results
    
    def _get_tier_latency(self, tier: TierType) -> str:
        """Get simulated latency for tier"""
        latencies = {
            TierType.HOT: "< 10ms",
            TierType.WARM: "50-200ms",
            TierType.COLD: "1-5s",
            TierType.ARCHIVE: "1-5min"
        }
        return latencies.get(tier, "unknown")
    
    def get_query_statistics(self) -> Dict:
        """Get query performance statistics"""
        total = self.performance_stats["total_queries"]
        if total == 0:
            return self.performance_stats
        
        stats = self.performance_stats.copy()
        stats["cache_hit_rate"] = round(stats["cache_hits"] / total * 100, 2)
        
        # Calculate tier distribution
        for tier in ["hot", "warm", "cold", "archive"]:
            tier_queries = stats[f"{tier}_queries"]
            stats[f"{tier}_percentage"] = round(tier_queries / total * 100, 2)
        
        return stats
    
    def clear_cache(self):
        """Clear query cache"""
        self.query_cache.clear()
        logger.info("Query cache cleared")
