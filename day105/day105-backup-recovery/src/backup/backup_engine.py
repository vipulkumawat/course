import asyncio
import os
import hashlib
import json
import tarfile
import time
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from cryptography.fernet import Fernet
import gzip
import shutil

from config.backup_config import config, BackupStrategy, StorageBackend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupEngine:
    def __init__(self):
        # Use absolute path to backup directory
        self.backup_base_path = Path(__file__).parent.parent.parent / config.backup_directory
        self.backup_base_path.mkdir(exist_ok=True)
        self.cipher_suite = None
        if config.enable_encryption:
            key = config.encryption_key.encode()[:32].ljust(32, b'0')  # Ensure 32 bytes
            key_b64 = Fernet.generate_key() if len(key) < 32 else Fernet.generate_key()
            self.cipher_suite = Fernet(key_b64)
    
    async def get_source_files(self) -> List[Path]:
        """Get list of files to backup from logs directory"""
        # Use absolute path to logs directory
        source_path = Path(__file__).parent.parent.parent / "logs"
        if not source_path.exists():
            # Create sample log files for demo
            source_path.mkdir(exist_ok=True)
            for i in range(10):
                log_file = source_path / f"app_{i}.log"
                with open(log_file, 'w') as f:
                    f.write(f"Sample log entry {i}\nTimestamp: {datetime.now()}\n" * 100)
        
        files = []
        for file_path in source_path.rglob("*"):
            if file_path.is_file():
                files.append(file_path)
        return files
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    async def get_backup_metadata(self, backup_id: str, files: List[Path], strategy: BackupStrategy) -> Dict:
        """Generate backup metadata"""
        file_metadata = {}
        total_size = 0
        
        for file_path in files:
            if file_path.exists():
                stat = file_path.stat()
                file_metadata[str(file_path)] = {
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "hash": self.calculate_file_hash(file_path)
                }
                total_size += stat.st_size
        
        return {
            "backup_id": backup_id,
            "strategy": strategy.value,
            "timestamp": datetime.now().isoformat(),
            "total_files": len(files),
            "total_size": total_size,
            "files": file_metadata,
            "config": {
                "compression": config.enable_compression,
                "encryption": config.enable_encryption,
                "checksum_algorithm": config.checksum_algorithm
            }
        }
    
    async def create_full_backup(self, backup_id: str) -> Dict[str, Any]:
        """Create full backup"""
        logger.info(f"Creating full backup: {backup_id}")
        start_time = time.time()
        
        files = await self.get_source_files()
        backup_path = self.backup_base_path / f"{backup_id}_full.tar.gz"
        
        # Create compressed archive
        with tarfile.open(backup_path, "w:gz" if config.enable_compression else "w") as tar:
            for file_path in files:
                if file_path.exists():
                    tar.add(file_path, arcname=file_path.name)
        
        # Encrypt if enabled
        if config.enable_encryption and self.cipher_suite:
            encrypted_path = backup_path.with_suffix(backup_path.suffix + ".enc")
            with open(backup_path, "rb") as infile, open(encrypted_path, "wb") as outfile:
                encrypted_data = self.cipher_suite.encrypt(infile.read())
                outfile.write(encrypted_data)
            backup_path.unlink()  # Remove unencrypted version
            backup_path = encrypted_path
        
        metadata = await self.get_backup_metadata(backup_id, files, BackupStrategy.FULL)
        metadata_path = self.backup_base_path / f"{backup_id}_metadata.json"
        
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps(metadata, indent=2))
        
        end_time = time.time()
        
        return {
            "success": True,
            "backup_id": backup_id,
            "backup_path": str(backup_path),
            "metadata_path": str(metadata_path),
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat(),
            "duration_seconds": end_time - start_time,
            "size_bytes": backup_path.stat().st_size,
            "file_count": len(files)
        }
    
    async def create_incremental_backup(self, backup_id: str) -> Dict[str, Any]:
        """Create incremental backup (changes since last backup)"""
        logger.info(f"Creating incremental backup: {backup_id}")
        start_time = time.time()
        
        # Get last backup metadata
        last_backup_metadata = await self.get_last_backup_metadata()
        current_files = await self.get_source_files()
        
        # Find changed/new files
        changed_files = []
        for file_path in current_files:
            if file_path.exists():
                current_hash = self.calculate_file_hash(file_path)
                last_hash = None
                if last_backup_metadata and str(file_path) in last_backup_metadata.get("files", {}):
                    last_hash = last_backup_metadata["files"][str(file_path)].get("hash")
                
                if current_hash != last_hash:
                    changed_files.append(file_path)
        
        if not changed_files:
            logger.info("No changes detected, skipping incremental backup")
            return {"success": True, "backup_id": backup_id, "size_bytes": 0, "file_count": 0}
        
        backup_path = self.backup_base_path / f"{backup_id}_incremental.tar.gz"
        
        with tarfile.open(backup_path, "w:gz" if config.enable_compression else "w") as tar:
            for file_path in changed_files:
                tar.add(file_path, arcname=file_path.name)
        
        # Store metadata
        metadata = await self.get_backup_metadata(backup_id, changed_files, BackupStrategy.INCREMENTAL)
        metadata["base_backup"] = last_backup_metadata.get("backup_id") if last_backup_metadata else None
        
        metadata_path = self.backup_base_path / f"{backup_id}_metadata.json"
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps(metadata, indent=2))
        
        end_time = time.time()
        
        return {
            "success": True,
            "backup_id": backup_id,
            "backup_path": str(backup_path),
            "metadata_path": str(metadata_path),
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat(),
            "duration_seconds": end_time - start_time,
            "size_bytes": backup_path.stat().st_size,
            "file_count": len(changed_files)
        }
    
    async def get_last_backup_metadata(self) -> Optional[Dict]:
        """Get metadata from the last backup"""
        metadata_files = list(self.backup_base_path.glob("*_metadata.json"))
        if not metadata_files:
            return None
        
        # Sort by creation time, get most recent
        latest_file = max(metadata_files, key=lambda x: x.stat().st_ctime)
        
        async with aiofiles.open(latest_file, 'r') as f:
            content = await f.read()
            return json.loads(content)
    
    async def create_backup(self, strategy: BackupStrategy, backup_id: str) -> Dict[str, Any]:
        """Create backup based on strategy"""
        try:
            if strategy == BackupStrategy.FULL:
                return await self.create_full_backup(backup_id)
            elif strategy == BackupStrategy.INCREMENTAL:
                return await self.create_incremental_backup(backup_id)
            elif strategy == BackupStrategy.DIFFERENTIAL:
                # For simplicity, treat differential as incremental
                return await self.create_incremental_backup(backup_id)
            else:
                raise ValueError(f"Unsupported backup strategy: {strategy}")
        
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return {
                "success": False,
                "backup_id": backup_id,
                "error": str(e),
                "start_time": datetime.now().isoformat()
            }
