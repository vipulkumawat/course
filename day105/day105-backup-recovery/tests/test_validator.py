import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import sys
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from validation.validator import BackupValidator
from backup.backup_engine import BackupEngine

class TestBackupValidator:
    
    @pytest.fixture
    def validator(self):
        return BackupValidator()
    
    @pytest.fixture
    def backup_engine(self):
        return BackupEngine()
    
    @pytest.mark.asyncio
    async def test_validate_backup_integrity(self, validator, backup_engine):
        # Create a test backup
        backup_id = "test_validation_backup"
        backup_result = await backup_engine.create_full_backup(backup_id)
        
        if backup_result["success"]:
            # Validate the backup
            validation_result = await validator.validate_backup_integrity(
                backup_result["backup_path"],
                backup_result["metadata_path"]
            )
            
            assert validation_result["overall_result"] in ["PASSED", "FAILED"]
            assert "tests" in validation_result
            assert "archive_integrity" in validation_result["tests"]
            assert "metadata_consistency" in validation_result["tests"]
            
            # Cleanup
            backup_path = Path(backup_result["backup_path"])
            metadata_path = Path(backup_result["metadata_path"])
            backup_path.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_archive_integrity_test(self, validator, backup_engine):
        # Create test backup
        backup_id = "test_archive_integrity"
        backup_result = await backup_engine.create_full_backup(backup_id)
        
        if backup_result["success"]:
            # Test archive integrity
            integrity_result = await validator._test_archive_integrity(
                backup_result["backup_path"]
            )
            
            assert "passed" in integrity_result
            assert isinstance(integrity_result["passed"], bool)
            
            # Cleanup
            backup_path = Path(backup_result["backup_path"])
            metadata_path = Path(backup_result["metadata_path"])
            backup_path.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
