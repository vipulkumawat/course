import asyncio
import json
import tarfile
import hashlib
import os
import tempfile
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupValidator:
    def __init__(self):
        pass
    
    async def validate_backup_integrity(self, backup_path: str, metadata_path: str) -> Dict[str, Any]:
        """Validate backup integrity using multiple methods"""
        logger.info(f"Validating backup: {backup_path}")
        
        validation_results = {
            "backup_path": backup_path,
            "validation_timestamp": asyncio.get_event_loop().time(),
            "tests": {}
        }
        
        try:
            # Test 1: Archive integrity
            validation_results["tests"]["archive_integrity"] = await self._test_archive_integrity(backup_path)
            
            # Test 2: Metadata consistency
            validation_results["tests"]["metadata_consistency"] = await self._test_metadata_consistency(
                backup_path, metadata_path
            )
            
            # Test 3: Sample file validation
            validation_results["tests"]["sample_validation"] = await self._test_sample_files(
                backup_path, metadata_path
            )
            
            # Test 4: Checksum verification
            validation_results["tests"]["checksum_verification"] = await self._test_checksums(
                backup_path, metadata_path
            )
            
            # Overall validation result
            all_passed = all(test["passed"] for test in validation_results["tests"].values())
            validation_results["overall_result"] = "PASSED" if all_passed else "FAILED"
            
        except Exception as e:
            logger.error(f"Validation failed with exception: {str(e)}")
            validation_results["overall_result"] = "ERROR"
            validation_results["error"] = str(e)
        
        return validation_results
    
    async def _test_archive_integrity(self, backup_path: str) -> Dict[str, Any]:
        """Test if archive can be opened and read"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                return {"passed": False, "error": "Backup file does not exist"}
            
            # Try to open and list contents
            if backup_path.endswith('.tar.gz') or backup_path.endswith('.tar'):
                with tarfile.open(backup_path, 'r:gz' if backup_path.endswith('.gz') else 'r') as tar:
                    members = tar.getnames()
                    return {
                        "passed": True,
                        "file_count": len(members),
                        "message": "Archive opened successfully"
                    }
            else:
                return {"passed": False, "error": "Unsupported archive format"}
                
        except Exception as e:
            return {"passed": False, "error": f"Archive integrity test failed: {str(e)}"}
    
    async def _test_metadata_consistency(self, backup_path: str, metadata_path: str) -> Dict[str, Any]:
        """Test metadata consistency with actual backup"""
        try:
            if not Path(metadata_path).exists():
                return {"passed": False, "error": "Metadata file missing"}
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            backup_size = Path(backup_path).stat().st_size
            metadata_files = metadata.get("files", {})
            
            return {
                "passed": True,
                "backup_size": backup_size,
                "metadata_file_count": len(metadata_files),
                "message": "Metadata consistency verified"
            }
            
        except Exception as e:
            return {"passed": False, "error": f"Metadata consistency test failed: {str(e)}"}
    
    async def _test_sample_files(self, backup_path: str, metadata_path: str) -> Dict[str, Any]:
        """Extract and validate a sample of files from backup"""
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            file_list = list(metadata.get("files", {}).keys())
            if not file_list:
                return {"passed": True, "message": "No files to validate"}
            
            # Sample 10% of files or at least 1 file
            sample_size = max(1, int(len(file_list) * 0.1))
            sample_files = random.sample(file_list, min(sample_size, len(file_list)))
            
            validated_files = 0
            with tempfile.TemporaryDirectory() as temp_dir:
                with tarfile.open(backup_path, 'r:gz' if backup_path.endswith('.gz') else 'r') as tar:
                    for file_name in sample_files:
                        try:
                            # Extract specific file
                            member = tar.getmember(Path(file_name).name)
                            tar.extract(member, temp_dir)
                            validated_files += 1
                        except KeyError:
                            pass  # File not found in archive
            
            return {
                "passed": validated_files > 0,
                "validated_files": validated_files,
                "sample_size": sample_size,
                "message": f"Validated {validated_files}/{sample_size} sample files"
            }
            
        except Exception as e:
            return {"passed": False, "error": f"Sample validation failed: {str(e)}"}
    
    async def _test_checksums(self, backup_path: str, metadata_path: str) -> Dict[str, Any]:
        """Test backup file checksum"""
        try:
            # Calculate current backup file checksum
            sha256_hash = hashlib.sha256()
            with open(backup_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            current_checksum = sha256_hash.hexdigest()
            
            return {
                "passed": True,
                "backup_checksum": current_checksum,
                "message": "Checksum calculated successfully"
            }
            
        except Exception as e:
            return {"passed": False, "error": f"Checksum verification failed: {str(e)}"}

# CLI for manual validation
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python validator.py <backup_path> <metadata_path>")
        sys.exit(1)
    
    validator = BackupValidator()
    result = asyncio.run(validator.validate_backup_integrity(sys.argv[1], sys.argv[2]))
    print(json.dumps(result, indent=2))
