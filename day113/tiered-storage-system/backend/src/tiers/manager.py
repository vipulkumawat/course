import asyncio
import os
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum
import aiofiles
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..metadata.models import LogEntry, StorageTier
from ..storage.backends import get_storage_backend
from ..policies.engine import PolicyEngine, TierType

logger = structlog.get_logger()

class TierManager:
    def __init__(self, config: Dict):
        self.config = config
        self.policy_engine = PolicyEngine(config)
        self.storage_backends = {
            TierType.HOT: get_storage_backend("ssd", config["HOT_STORAGE_PATH"]),
            TierType.WARM: get_storage_backend("standard", config["WARM_STORAGE_PATH"]),
            TierType.COLD: get_storage_backend("hdd", config["COLD_STORAGE_PATH"]),
            TierType.ARCHIVE: get_storage_backend("tape", config["ARCHIVE_STORAGE_PATH"])
        }
        self.migration_stats = {
            "total_migrated": 0,
            "bytes_migrated": 0,
            "cost_savings": 0.0,
            "last_migration": None
        }
    
    async def store_log_entry(self, log_data: Dict, tier: TierType = TierType.HOT) -> str:
        """Store a new log entry in the specified tier"""
        entry_id = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(log_data)) % 10000}"
        
        # Add metadata
        log_data.update({
            "entry_id": entry_id,
            "stored_at": datetime.now().isoformat(),
            "tier": tier.value,
            "size_bytes": len(json.dumps(log_data))
        })
        
        # Store in appropriate backend
        backend = self.storage_backends[tier]
        await backend.write(entry_id, json.dumps(log_data))
        
        logger.info("Log entry stored", entry_id=entry_id, tier=tier.value)
        return entry_id
    
    async def migrate_data(self, from_tier: TierType, to_tier: TierType, entry_ids: List[str]) -> Dict:
        """Migrate data between tiers"""
        migrated_count = 0
        total_bytes = 0
        errors = []
        
        source_backend = self.storage_backends[from_tier]
        target_backend = self.storage_backends[to_tier]
        
        for entry_id in entry_ids:
            try:
                # Read from source tier
                data = await source_backend.read(entry_id)
                if data is None:
                    continue
                
                log_data = json.loads(data)
                log_data["tier"] = to_tier.value
                log_data["migrated_at"] = datetime.now().isoformat()
                
                # Write to target tier
                await target_backend.write(entry_id, json.dumps(log_data))
                
                # Verify migration
                verification = await target_backend.read(entry_id)
                if verification:
                    # Remove from source tier
                    await source_backend.delete(entry_id)
                    migrated_count += 1
                    total_bytes += log_data.get("size_bytes", 0)
                    
                    logger.info("Data migrated", 
                               entry_id=entry_id, 
                               from_tier=from_tier.value, 
                               to_tier=to_tier.value)
                
            except Exception as e:
                errors.append(f"Failed to migrate {entry_id}: {str(e)}")
                logger.error("Migration failed", entry_id=entry_id, error=str(e))
        
        # Calculate cost savings
        cost_savings = self._calculate_cost_savings(total_bytes, from_tier, to_tier)
        
        # Update statistics
        self.migration_stats["total_migrated"] += migrated_count
        self.migration_stats["bytes_migrated"] += total_bytes
        self.migration_stats["cost_savings"] += cost_savings
        self.migration_stats["last_migration"] = datetime.now().isoformat()
        
        return {
            "migrated_count": migrated_count,
            "total_bytes": total_bytes,
            "cost_savings": cost_savings,
            "errors": errors
        }
    
    async def evaluate_migration_candidates(self) -> Dict[Tuple[TierType, TierType], List[str]]:
        """Find data eligible for tier migration"""
        candidates = {}
        
        # Check each tier for migration candidates
        for tier in [TierType.HOT, TierType.WARM, TierType.COLD]:
            next_tier = self._get_next_tier(tier)
            if next_tier:
                eligible_entries = await self._get_migration_candidates(tier, next_tier)
                if eligible_entries:
                    candidates[(tier, next_tier)] = eligible_entries
        
        return candidates
    
    async def _get_migration_candidates(self, from_tier: TierType, to_tier: TierType) -> List[str]:
        """Get entries eligible for migration from one tier to another"""
        backend = self.storage_backends[from_tier]
        all_entries = await backend.list_entries()
        
        eligible = []
        cutoff_date = self._get_migration_cutoff_date(from_tier, to_tier)
        
        for entry_id in all_entries:
            try:
                data = await backend.read(entry_id)
                if data:
                    log_data = json.loads(data)
                    stored_at = datetime.fromisoformat(log_data.get("stored_at", datetime.now().isoformat()))
                    
                    if stored_at < cutoff_date:
                        # Check access patterns
                        if await self.policy_engine.should_migrate(log_data, from_tier, to_tier):
                            eligible.append(entry_id)
            except Exception as e:
                logger.error("Error evaluating entry", entry_id=entry_id, error=str(e))
        
        return eligible[:self.config.get("MIGRATION_BATCH_SIZE", 1000)]
    
    def _get_next_tier(self, tier: TierType) -> Optional[TierType]:
        """Get the next tier in the hierarchy"""
        tier_order = [TierType.HOT, TierType.WARM, TierType.COLD, TierType.ARCHIVE]
        try:
            current_index = tier_order.index(tier)
            if current_index < len(tier_order) - 1:
                return tier_order[current_index + 1]
        except (ValueError, IndexError):
            pass
        return None
    
    def _get_migration_cutoff_date(self, from_tier: TierType, to_tier: TierType) -> datetime:
        """Get cutoff date for tier migration"""
        if from_tier == TierType.HOT and to_tier == TierType.WARM:
            return datetime.now() - timedelta(days=self.config.get("HOT_TO_WARM_DAYS", 7))
        elif from_tier == TierType.WARM and to_tier == TierType.COLD:
            return datetime.now() - timedelta(days=self.config.get("WARM_TO_COLD_DAYS", 30))
        elif from_tier == TierType.COLD and to_tier == TierType.ARCHIVE:
            return datetime.now() - timedelta(days=self.config.get("COLD_TO_ARCHIVE_DAYS", 365))
        
        return datetime.now()
    
    def _calculate_cost_savings(self, bytes_migrated: int, from_tier: TierType, to_tier: TierType) -> float:
        """Calculate monthly cost savings from tier migration"""
        tier_costs = {
            TierType.HOT: self.config.get("HOT_TIER_COST", 200.0),
            TierType.WARM: self.config.get("WARM_TIER_COST", 50.0),
            TierType.COLD: self.config.get("COLD_TIER_COST", 10.0),
            TierType.ARCHIVE: self.config.get("ARCHIVE_TIER_COST", 1.0)
        }
        
        tb_migrated = bytes_migrated / (1024 ** 4)  # Convert to TB
        from_cost = tier_costs[from_tier] * tb_migrated
        to_cost = tier_costs[to_tier] * tb_migrated
        
        return from_cost - to_cost
    
    async def get_tier_statistics(self) -> Dict:
        """Get comprehensive tier statistics"""
        stats = {}
        
        for tier in TierType:
            backend = self.storage_backends[tier]
            entries = await backend.list_entries()
            total_size = 0
            
            for entry_id in entries:
                data = await backend.read(entry_id)
                if data:
                    log_data = json.loads(data)
                    total_size += log_data.get("size_bytes", 0)
            
            stats[tier.value] = {
                "entry_count": len(entries),
                "total_size_bytes": total_size,
                "total_size_gb": round(total_size / (1024 ** 3), 2),
                "monthly_cost": self._calculate_tier_cost(total_size, tier)
            }
        
        stats["migration_stats"] = self.migration_stats
        return stats
    
    def _calculate_tier_cost(self, size_bytes: int, tier: TierType) -> float:
        """Calculate monthly cost for tier storage"""
        tier_costs = {
            TierType.HOT: self.config.get("HOT_TIER_COST", 200.0),
            TierType.WARM: self.config.get("WARM_TIER_COST", 50.0),
            TierType.COLD: self.config.get("COLD_TIER_COST", 10.0),
            TierType.ARCHIVE: self.config.get("ARCHIVE_TIER_COST", 1.0)
        }
        
        tb_size = size_bytes / (1024 ** 4)
        return tier_costs[tier] * tb_size

# Initialize global tier manager
tier_manager = None

def get_tier_manager(config: Dict) -> TierManager:
    global tier_manager
    if tier_manager is None:
        tier_manager = TierManager(config)
    return tier_manager
