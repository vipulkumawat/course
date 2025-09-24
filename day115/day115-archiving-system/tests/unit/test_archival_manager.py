import pytest
import asyncio
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.archival.manager import ArchivalManager, LogEntry
from config.archival_config import config

@pytest.fixture
def manager():
    return ArchivalManager(config)

@pytest.fixture
def sample_log_entries():
    return [
        LogEntry(
            id="test_1",
            timestamp=datetime.now(),
            level="INFO",
            service="test",
            message="Test message",
            metadata={"key": "value"},
            size_bytes=100,
            file_path="/test/path"
        )
    ]

@pytest.mark.asyncio
async def test_create_archival_job(manager, sample_log_entries):
    job = await manager.create_archival_job(sample_log_entries)
    
    assert job.job_id in manager.jobs
    assert len(job.entries) == 1
    assert job.status == "created"

@pytest.mark.asyncio
async def test_validate_entries(manager, sample_log_entries):
    # Should not raise exception for valid entries
    await manager._validate_entries(sample_log_entries)
    
    # Should raise exception for invalid entries
    invalid_entry = LogEntry(
        id="",  # Invalid empty ID
        timestamp=datetime.now(),
        level="INFO",
        service="test",
        message="Test",
        metadata={},
        size_bytes=100,
        file_path="/test"
    )
    
    with pytest.raises(ValueError):
        await manager._validate_entries([invalid_entry])

@pytest.mark.asyncio
async def test_compress_entries(manager, sample_log_entries):
    compressed_data = await manager._compress_entries(sample_log_entries)
    
    assert isinstance(compressed_data, bytes)
    assert len(compressed_data) > 0
    # Compressed data should be smaller than original JSON
    assert len(compressed_data) < 1000

def test_get_statistics(manager):
    stats = manager.get_statistics()
    
    assert "total_archived" in stats
    assert "compression_ratio" in stats
    assert isinstance(stats["total_archived"], int)
