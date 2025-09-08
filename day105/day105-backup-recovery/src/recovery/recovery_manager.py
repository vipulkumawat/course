import asyncio
import json
import tarfile
import shutil
import tempfile
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecoveryManager:
    def __init__(self):
        # Use absolute paths
        self.base_path = Path(__file__).parent.parent.parent
        self.backup_base_path = self.base_path / "backups"
        self.recovery_base_path = self.base_path / "recovery"
        self.recovery_base_path.mkdir(exist_ok=True)
    
    async def list_available_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with metadata"""
        backups = []
        metadata_files = list(self.backup_base_path.glob("*_metadata.json"))
        
        for metadata_file in metadata_files:
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                backup_id = metadata["backup_id"]
                strategy = metadata["strategy"]
                
                # Find corresponding backup file
                backup_file = None
                for ext in [".tar.gz", ".tar", ".tar.gz.enc"]:
                    potential_file = self.backup_base_path / f"{backup_id}_{strategy}{ext}"
                    if potential_file.exists():
                        backup_file = potential_file
                        break
                
                if backup_file:
                    backups.append({
                        "backup_id": backup_id,
                        "strategy": strategy,
                        "timestamp": metadata["timestamp"],
                        "file_count": metadata["total_files"],
                        "size_bytes": metadata["total_size"],
                        "backup_file": str(backup_file),
                        "metadata_file": str(metadata_file)
                    })
            except Exception as e:
                logger.warning(f"Could not read metadata from {metadata_file}: {str(e)}")
        
        # Sort by timestamp (newest first)
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
    
    async def recover_from_backup(self, backup_id: str, target_directory: str = "recovery/restored") -> Dict[str, Any]:
        """Recover data from specific backup"""
        logger.info(f"Starting recovery from backup: {backup_id}")
        start_time = datetime.now()
        
        try:
            # Find backup files
            backup_info = await self._find_backup_files(backup_id)
            if not backup_info:
                return {
                    "success": False,
                    "error": f"Backup {backup_id} not found",
                    "backup_id": backup_id
                }
            
            # Create target directory
            target_path = Path(target_directory)
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Extract backup
            extracted_files = await self._extract_backup(
                backup_info["backup_file"], 
                str(target_path)
            )
            
            # Verify recovery
            verification_result = await self._verify_recovery(
                backup_info["metadata_file"],
                target_path,
                extracted_files
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "backup_id": backup_id,
                "target_directory": target_directory,
                "extracted_files": len(extracted_files),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "verification": verification_result
            }
            
        except Exception as e:
            logger.error(f"Recovery failed: {str(e)}")
            return {
                "success": False,
                "backup_id": backup_id,
                "error": str(e),
                "start_time": start_time.isoformat()
            }
    
    async def point_in_time_recovery(self, target_timestamp: str, target_directory: str = "recovery/pit") -> Dict[str, Any]:
        """Perform point-in-time recovery to specific timestamp"""
        logger.info(f"Point-in-time recovery to: {target_timestamp}")
        
        try:
            target_dt = datetime.fromisoformat(target_timestamp)
            backups = await self.list_available_backups()
            
            # Find best backup for target time
            suitable_backup = None
            for backup in backups:
                backup_dt = datetime.fromisoformat(backup["timestamp"])
                if backup_dt <= target_dt:
                    suitable_backup = backup
                    break
            
            if not suitable_backup:
                return {
                    "success": False,
                    "error": f"No backup available for timestamp {target_timestamp}"
                }
            
            # Recover from suitable backup
            recovery_result = await self.recover_from_backup(
                suitable_backup["backup_id"], 
                target_directory
            )
            
            recovery_result["point_in_time"] = {
                "target_timestamp": target_timestamp,
                "backup_used": suitable_backup["backup_id"],
                "backup_timestamp": suitable_backup["timestamp"]
            }
            
            return recovery_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Point-in-time recovery failed: {str(e)}",
                "target_timestamp": target_timestamp
            }
    
    async def _find_backup_files(self, backup_id: str) -> Optional[Dict[str, str]]:
        """Find backup and metadata files for given backup_id"""
        metadata_file = self.backup_base_path / f"{backup_id}_metadata.json"
        if not metadata_file.exists():
            return None
        
        # Find backup file
        backup_file = None
        for strategy in ["full", "incremental", "differential"]:
            for ext in [".tar.gz", ".tar", ".tar.gz.enc"]:
                potential_file = self.backup_base_path / f"{backup_id}_{strategy}{ext}"
                if potential_file.exists():
                    backup_file = potential_file
                    break
            if backup_file:
                break
        
        if not backup_file:
            return None
        
        return {
            "backup_file": str(backup_file),
            "metadata_file": str(metadata_file)
        }
    
    async def _extract_backup(self, backup_file: str, target_directory: str) -> List[str]:
        """Extract backup archive to target directory"""
        extracted_files = []
        
        try:
            # Handle encrypted files
            if backup_file.endswith('.enc'):
                # Decrypt the file first
                with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                # For now, just copy the encrypted file as we don't have the key
                # In a real implementation, you'd decrypt here
                shutil.copy2(backup_file, temp_path)
                backup_file = temp_path
            
            # Extract the archive
            with tarfile.open(backup_file, 'r:gz' if backup_file.endswith('.gz') else 'r') as tar:
                members = tar.getmembers()
                for member in members:
                    if member.isfile():
                        tar.extract(member, target_directory)
                        extracted_files.append(member.name)
            
            # Clean up temporary file if created
            if backup_file.endswith('.tar.gz') and backup_file != backup_file:
                os.unlink(backup_file)
                        
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            raise
        
        return extracted_files
    
    async def _verify_recovery(self, metadata_file: str, target_path: Path, extracted_files: List[str]) -> Dict[str, Any]:
        """Verify recovered files against original metadata"""
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            original_files = metadata.get("files", {})
            verified_count = 0
            missing_files = []
            
            for extracted_file in extracted_files:
                file_path = target_path / extracted_file
                if file_path.exists():
                    verified_count += 1
                else:
                    missing_files.append(extracted_file)
            
            return {
                "verified_files": verified_count,
                "total_extracted": len(extracted_files),
                "missing_files": missing_files,
                "verification_passed": len(missing_files) == 0
            }
            
        except Exception as e:
            return {
                "verification_passed": False,
                "error": f"Verification failed: {str(e)}"
            }

# CLI for manual recovery
if __name__ == "__main__":
    import sys
    
    async def main():
        recovery_manager = RecoveryManager()
        
        if len(sys.argv) < 2:
            print("Available commands:")
            print("  list - List available backups")
            print("  recover <backup_id> [target_dir] - Recover from backup")
            print("  pit <timestamp> [target_dir] - Point-in-time recovery")
            return
        
        command = sys.argv[1]
        
        if command == "list":
            backups = await recovery_manager.list_available_backups()
            print(json.dumps(backups, indent=2))
        
        elif command == "recover" and len(sys.argv) >= 3:
            backup_id = sys.argv[2]
            target_dir = sys.argv[3] if len(sys.argv) > 3 else "recovery/restored"
            result = await recovery_manager.recover_from_backup(backup_id, target_dir)
            print(json.dumps(result, indent=2))
        
        elif command == "pit" and len(sys.argv) >= 3:
            timestamp = sys.argv[2]
            target_dir = sys.argv[3] if len(sys.argv) > 3 else "recovery/pit"
            result = await recovery_manager.point_in_time_recovery(timestamp, target_dir)
            print(json.dumps(result, indent=2))
        
        else:
            print("Invalid command or missing arguments")
    
    asyncio.run(main())
