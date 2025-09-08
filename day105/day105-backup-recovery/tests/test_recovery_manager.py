import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import sys
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from recovery.recovery_manager import RecoveryManager
from backup.backup_engine import BackupEngine
from config.backup_config import BackupStrategy

class TestRecoveryManager:
    
    @pytest.fixture
    def recovery_manager(self):
        return RecoveryManager()
    
    @pytest.fixture
    def backup_engine(self):
        return BackupEngine()
    
    @pytest.mark.asyncio
    async def test_list_available_backups(self, recovery_manager):
        backups = await recovery_manager.list_available_backups()
        assert isinstance(backups, list)
    
    @pytest.mark.asyncio
    async def test_recovery_workflow(self, recovery_manager, backup_engine):
        # Create a test backup first
        backup_id = "test_recovery_backup"
        backup_result = await backup_engine.create_full_backup(backup_id)
        
        if backup_result["success"]:
            # Test recovery
            recovery_result = await recovery_manager.recover_from_backup(
                backup_id, 
                "tests/temp_recovery"
            )
            
            assert recovery_result["success"] == True
            assert recovery_result["backup_id"] == backup_id
            assert recovery_result["extracted_files"] > 0
            
            # Cleanup
            recovery_path = Path("tests/temp_recovery")
            if recovery_path.exists():
                shutil.rmtree(recovery_path)
            
            # Cleanup backup files
            backup_path = Path(backup_result["backup_path"])
            metadata_path = Path(backup_result["metadata_path"])
            backup_path.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_point_in_time_recovery(self, recovery_manager, backup_engine):
        # Create backup
        backup_id = "test_pit_backup"
        backup_result = await backup_engine.create_full_backup(backup_id)
        
        if backup_result["success"]:
            # Test point-in-time recovery
            from datetime import datetime
            target_timestamp = datetime.now().isoformat()
            
            pit_result = await recovery_manager.point_in_time_recovery(
                target_timestamp,
                "tests/temp_pit_recovery"
            )
            
            assert pit_result["success"] == True
            assert "point_in_time" in pit_result
            
            # Cleanup
            recovery_path = Path("tests/temp_pit_recovery")
            if recovery_path.exists():
                shutil.rmtree(recovery_path)
            
            backup_path = Path(backup_result["backup_path"])
            metadata_path = Path(backup_result["metadata_path"])
            backup_path.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
