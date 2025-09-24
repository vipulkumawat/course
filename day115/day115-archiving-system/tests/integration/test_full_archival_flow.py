import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.archival.manager import ArchivalManager, LogEntry
from src.archival.scheduler import ArchivalScheduler
from src.storage.managers import StorageTierManager
from config.archival_config import config

@pytest.fixture
def temp_dir():
    temp_dir = tempfile.mkdtemp()
    original_cwd = Path.cwd()
    
    # Change to temp directory for test
    import os
    os.chdir(temp_dir)
    
    yield Path(temp_dir)
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_end_to_end_archival(temp_dir):
    """Test complete archival workflow"""
    
    # Create components
    manager = ArchivalManager(config)
    storage_manager = StorageTierManager(config)
    scheduler = ArchivalScheduler(manager, config)
    
    # Create test log files
    logs_dir = temp_dir / "logs"
    logs_dir.mkdir()
    
    test_logs = [
        {"timestamp": "2025-05-01T10:00:00Z", "level": "INFO", "service": "test", "message": "Test 1"},
        {"timestamp": "2025-05-01T10:01:00Z", "level": "ERROR", "service": "test", "message": "Test 2"},
        {"timestamp": "2025-05-01T10:02:00Z", "level": "WARN", "service": "test", "message": "Test 3"}
    ]
    
    log_file = logs_dir / "test.log"
    with open(log_file, 'w') as f:
        for log in test_logs:
            f.write(json.dumps(log) + '\n')
    
    # Make file old enough for archival
    import os, time
    old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days ago
    os.utime(log_file, (old_time, old_time))
    
    # Run archival cycle
    await scheduler.run_archival_cycle()
    
    # Verify results
    archives_dir = temp_dir / "archives"
    assert archives_dir.exists()
    
    # Check that archives were created
    archive_files = list(archives_dir.rglob("*.zst"))
    assert len(archive_files) > 0
    
    # Check metadata was created
    metadata_dir = temp_dir / "metadata"
    assert metadata_dir.exists()
    
    metadata_files = list(metadata_dir.glob("*_meta.json"))
    assert len(metadata_files) > 0
    
    # Verify original log was moved to archived directory
    archived_dir = logs_dir / "archived"
    assert archived_dir.exists()
    assert (archived_dir / "test.log").exists()

@pytest.mark.asyncio
async def test_storage_tier_management(temp_dir):
    """Test storage tier functionality"""
    
    storage_manager = StorageTierManager(config)
    
    # Test tier determination
    hot_tier = await storage_manager.get_appropriate_tier(5)  # 5 days old
    assert hot_tier == "hot"
    
    warm_tier = await storage_manager.get_appropriate_tier(60)  # 60 days old
    assert warm_tier == "warm"
    
    cold_tier = await storage_manager.get_appropriate_tier(200)  # 200 days old
    assert cold_tier == "cold"
    
    deep_tier = await storage_manager.get_appropriate_tier(400)  # 400 days old
    assert deep_tier == "deep"
    
    # Test statistics
    stats = await storage_manager.get_tier_statistics()
    assert "hot" in stats
    assert "warm" in stats
    assert "cold" in stats
    assert "deep" in stats
