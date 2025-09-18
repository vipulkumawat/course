import pytest
import asyncio
import json
from src.tiers.manager import TierManager
from src.policies.engine import TierType

@pytest.fixture
def config():
    return {
        "HOT_STORAGE_PATH": "./test_data/hot",
        "WARM_STORAGE_PATH": "./test_data/warm",
        "COLD_STORAGE_PATH": "./test_data/cold", 
        "ARCHIVE_STORAGE_PATH": "./test_data/archive",
        "HOT_TO_WARM_DAYS": 7,
        "WARM_TO_COLD_DAYS": 30,
        "COLD_TO_ARCHIVE_DAYS": 365,
        "MIGRATION_BATCH_SIZE": 100
    }

@pytest.fixture
def tier_manager(config):
    return TierManager(config)

@pytest.mark.asyncio
async def test_store_log_entry(tier_manager):
    """Test storing a log entry"""
    log_data = {
        "message": "Test log message",
        "level": "INFO",
        "service": "test-service"
    }
    
    entry_id = await tier_manager.store_log_entry(log_data, TierType.HOT)
    assert entry_id is not None
    assert entry_id.startswith("log_")

@pytest.mark.asyncio
async def test_get_tier_statistics(tier_manager):
    """Test getting tier statistics"""
    stats = await tier_manager.get_tier_statistics()
    
    assert "migration_stats" in stats
    assert "hot" in stats
    assert "warm" in stats
    assert "cold" in stats
    assert "archive" in stats

@pytest.mark.asyncio
async def test_migration_candidates(tier_manager):
    """Test finding migration candidates"""
    candidates = await tier_manager.evaluate_migration_candidates()
    
    assert isinstance(candidates, dict)
    # Should be empty initially since no data exists yet
