import os
import json
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any
import aiofiles
import structlog

logger = structlog.get_logger()

class StorageBackend(ABC):
    """Abstract storage backend interface"""
    
    @abstractmethod
    async def write(self, key: str, data: str) -> bool:
        pass
    
    @abstractmethod
    async def read(self, key: str) -> Optional[str]:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def list_entries(self) -> List[str]:
        pass

class SSDBackend(StorageBackend):
    """High-performance SSD storage backend"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.performance_cache = {}  # In-memory cache for hot data
    
    async def write(self, key: str, data: str) -> bool:
        try:
            file_path = self.base_path / f"{key}.json"
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(data)
            
            # Cache hot data in memory
            self.performance_cache[key] = data
            logger.info("SSD write completed", key=key, path=str(file_path))
            return True
        except Exception as e:
            logger.error("SSD write failed", key=key, error=str(e))
            return False
    
    async def read(self, key: str) -> Optional[str]:
        # Check cache first
        if key in self.performance_cache:
            logger.info("SSD cache hit", key=key)
            return self.performance_cache[key]
        
        try:
            file_path = self.base_path / f"{key}.json"
            if file_path.exists():
                async with aiofiles.open(file_path, 'r') as f:
                    data = await f.read()
                
                # Cache for next access
                self.performance_cache[key] = data
                logger.info("SSD read completed", key=key)
                return data
        except Exception as e:
            logger.error("SSD read failed", key=key, error=str(e))
        
        return None
    
    async def delete(self, key: str) -> bool:
        try:
            file_path = self.base_path / f"{key}.json"
            if file_path.exists():
                file_path.unlink()
            
            # Remove from cache
            self.performance_cache.pop(key, None)
            logger.info("SSD delete completed", key=key)
            return True
        except Exception as e:
            logger.error("SSD delete failed", key=key, error=str(e))
            return False
    
    async def list_entries(self) -> List[str]:
        try:
            entries = []
            for file_path in self.base_path.glob("*.json"):
                entries.append(file_path.stem)
            return entries
        except Exception as e:
            logger.error("SSD list failed", error=str(e))
            return []

class StandardBackend(StorageBackend):
    """Standard storage backend"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def write(self, key: str, data: str) -> bool:
        try:
            file_path = self.base_path / f"{key}.json"
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(data)
            
            # Simulate standard storage delay
            await asyncio.sleep(0.01)
            logger.info("Standard write completed", key=key)
            return True
        except Exception as e:
            logger.error("Standard write failed", key=key, error=str(e))
            return False
    
    async def read(self, key: str) -> Optional[str]:
        try:
            file_path = self.base_path / f"{key}.json"
            if file_path.exists():
                # Simulate standard storage delay
                await asyncio.sleep(0.05)
                
                async with aiofiles.open(file_path, 'r') as f:
                    data = await f.read()
                
                logger.info("Standard read completed", key=key)
                return data
        except Exception as e:
            logger.error("Standard read failed", key=key, error=str(e))
        
        return None
    
    async def delete(self, key: str) -> bool:
        try:
            file_path = self.base_path / f"{key}.json"
            if file_path.exists():
                file_path.unlink()
            logger.info("Standard delete completed", key=key)
            return True
        except Exception as e:
            logger.error("Standard delete failed", key=key, error=str(e))
            return False
    
    async def list_entries(self) -> List[str]:
        try:
            entries = []
            for file_path in self.base_path.glob("*.json"):
                entries.append(file_path.stem)
            return entries
        except Exception as e:
            logger.error("Standard list failed", error=str(e))
            return []

class HDDBackend(StorageBackend):
    """HDD storage backend with higher latency"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def write(self, key: str, data: str) -> bool:
        try:
            file_path = self.base_path / f"{key}.json"
            
            # Simulate HDD seek time
            await asyncio.sleep(0.1)
            
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(data)
            
            logger.info("HDD write completed", key=key)
            return True
        except Exception as e:
            logger.error("HDD write failed", key=key, error=str(e))
            return False
    
    async def read(self, key: str) -> Optional[str]:
        try:
            file_path = self.base_path / f"{key}.json"
            if file_path.exists():
                # Simulate HDD seek and read time
                await asyncio.sleep(0.2)
                
                async with aiofiles.open(file_path, 'r') as f:
                    data = await f.read()
                
                logger.info("HDD read completed", key=key)
                return data
        except Exception as e:
            logger.error("HDD read failed", key=key, error=str(e))
        
        return None
    
    async def delete(self, key: str) -> bool:
        try:
            file_path = self.base_path / f"{key}.json"
            if file_path.exists():
                await asyncio.sleep(0.05)  # Simulate delete time
                file_path.unlink()
            logger.info("HDD delete completed", key=key)
            return True
        except Exception as e:
            logger.error("HDD delete failed", key=key, error=str(e))
            return False
    
    async def list_entries(self) -> List[str]:
        try:
            # Simulate directory scan time
            await asyncio.sleep(0.1)
            entries = []
            for file_path in self.base_path.glob("*.json"):
                entries.append(file_path.stem)
            return entries
        except Exception as e:
            logger.error("HDD list failed", error=str(e))
            return []

class TapeBackend(StorageBackend):
    """Tape/Archive storage backend with very high latency"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.archive_metadata = {}
    
    async def write(self, key: str, data: str) -> bool:
        try:
            file_path = self.base_path / f"{key}.json"
            
            # Simulate tape mount and positioning time
            await asyncio.sleep(1.0)
            
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(data)
            
            # Update archive metadata
            self.archive_metadata[key] = {
                "archived_at": datetime.now().isoformat(),
                "size_bytes": len(data)
            }
            
            logger.info("Tape write completed", key=key)
            return True
        except Exception as e:
            logger.error("Tape write failed", key=key, error=str(e))
            return False
    
    async def read(self, key: str) -> Optional[str]:
        try:
            file_path = self.base_path / f"{key}.json"
            if file_path.exists():
                # Simulate tape mount, seek, and read time
                await asyncio.sleep(3.0)
                
                async with aiofiles.open(file_path, 'r') as f:
                    data = await f.read()
                
                logger.info("Tape read completed", key=key)
                return data
        except Exception as e:
            logger.error("Tape read failed", key=key, error=str(e))
        
        return None
    
    async def delete(self, key: str) -> bool:
        try:
            file_path = self.base_path / f"{key}.json"
            if file_path.exists():
                await asyncio.sleep(0.5)  # Simulate tape positioning
                file_path.unlink()
            
            self.archive_metadata.pop(key, None)
            logger.info("Tape delete completed", key=key)
            return True
        except Exception as e:
            logger.error("Tape delete failed", key=key, error=str(e))
            return False
    
    async def list_entries(self) -> List[str]:
        try:
            # Simulate tape catalog scan
            await asyncio.sleep(2.0)
            entries = []
            for file_path in self.base_path.glob("*.json"):
                entries.append(file_path.stem)
            return entries
        except Exception as e:
            logger.error("Tape list failed", error=str(e))
            return []

def get_storage_backend(backend_type: str, base_path: str) -> StorageBackend:
    """Factory function to get appropriate storage backend"""
    backends = {
        "ssd": SSDBackend,
        "standard": StandardBackend,
        "hdd": HDDBackend,
        "tape": TapeBackend
    }
    
    backend_class = backends.get(backend_type, StandardBackend)
    return backend_class(base_path)
