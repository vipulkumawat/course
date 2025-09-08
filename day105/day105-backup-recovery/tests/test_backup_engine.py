import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import sys
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from backup.backup_engine import BackupEngine
from config.backup_config import BackupStrategy

class TestBackupEngine:
    
    @pytest.fixture
    def engine(self):
        return BackupEngine()
    
    @pytest.fixture
    def temp_backup_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_backup_engine_init(self, engine):
        assert engine is not None
        assert engine.backup_base_path.exists()
    
    @pytest.mark.asyncio
    async def test_get_source_files(self, engine):
        files = await engine.get_source_files()
        assert isinstance(files, list)
        assert len(files) > 0
    
    @pytest.mark.asyncio
    async def test_create_full_backup(self, engine):
        backup_id = "test_full_backup"
        result = await engine.create_full_backup(backup_id)
        
        assert result["success"] == True
        assert result["backup_id"] == backup_id
        assert result["file_count"] > 0
        assert result["size_bytes"] > 0
        
        # Verify backup file exists
        backup_path = Path(result["backup_path"])
        assert backup_path.exists()
        
        # Verify metadata exists
        metadata_path = Path(result["metadata_path"])
        assert metadata_path.exists()
        
        # Cleanup
        backup_path.unlink()
        metadata_path.unlink()
    
    @pytest.mark.asyncio
    async def test_create_incremental_backup(self, engine):
        # First create a full backup
        full_backup_id = "test_full_for_incremental"
        await engine.create_full_backup(full_backup_id)
        
        # Then create incremental
        incremental_backup_id = "test_incremental_backup"
        result = await engine.create_incremental_backup(incremental_backup_id)
        
        assert result["success"] == True
        assert result["backup_id"] == incremental_backup_id
        
        # Cleanup
        for file_pattern in ["test_full_for_incremental*", "test_incremental_backup*"]:
            for file_path in engine.backup_base_path.glob(file_pattern):
                file_path.unlink()
    
    def test_calculate_file_hash(self, engine, temp_backup_dir):
        # Create test file
        test_file = temp_backup_dir / "test.txt"
        test_content = "test content for hashing"
        test_file.write_text(test_content)
        
        hash_result = engine.calculate_file_hash(test_file)
        assert len(hash_result) == 64  # SHA256 hex length
        assert isinstance(hash_result, str)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
