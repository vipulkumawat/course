import asyncio
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json
import redis
from config.backup_config import config, BackupStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupScheduler:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.running_backups: Dict[str, Dict] = {}
        self.lock_timeout = 300  # 5 minutes
        
    async def acquire_backup_lock(self, backup_type: str) -> bool:
        """Distributed lock to prevent concurrent backups"""
        lock_key = f"backup_lock:{backup_type}"
        lock_acquired = self.redis_client.set(
            lock_key, 
            datetime.now().isoformat(), 
            nx=True, 
            ex=self.lock_timeout
        )
        return bool(lock_acquired)
    
    def release_backup_lock(self, backup_type: str):
        """Release backup lock"""
        lock_key = f"backup_lock:{backup_type}"
        self.redis_client.delete(lock_key)
    
    async def schedule_backup(self, strategy: BackupStrategy):
        """Schedule and execute backup"""
        backup_id = f"{strategy.value}_{int(time.time())}"
        
        if not await self.acquire_backup_lock(strategy.value):
            logger.warning(f"Backup {strategy.value} already running, skipping")
            return
        
        try:
            logger.info(f"Starting {strategy.value} backup: {backup_id}")
            
            # Import here to avoid circular imports
            from backup.backup_engine import BackupEngine
            
            engine = BackupEngine()
            backup_result = await engine.create_backup(strategy, backup_id)
            
            # Record backup completion
            self.redis_client.hset(
                "backup_history",
                backup_id,
                json.dumps({
                    "strategy": strategy.value,
                    "start_time": backup_result.get("start_time"),
                    "end_time": backup_result.get("end_time"),
                    "size_bytes": backup_result.get("size_bytes", 0),
                    "status": "completed" if backup_result.get("success") else "failed",
                    "file_count": backup_result.get("file_count", 0)
                })
            )
            
            logger.info(f"Backup {backup_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Backup {backup_id} failed: {str(e)}")
            self.redis_client.hset(
                "backup_history",
                backup_id,
                json.dumps({
                    "strategy": strategy.value,
                    "start_time": datetime.now().isoformat(),
                    "status": "failed",
                    "error": str(e)
                })
            )
        finally:
            self.release_backup_lock(strategy.value)
    
    def setup_schedules(self):
        """Setup backup schedules"""
        # Schedule full backups
        schedule.every().sunday.at("02:00").do(
            lambda: asyncio.create_task(self.schedule_backup(BackupStrategy.FULL))
        )
        
        # Schedule incremental backups  
        schedule.every(6).hours.do(
            lambda: asyncio.create_task(self.schedule_backup(BackupStrategy.INCREMENTAL))
        )
        
        # Schedule differential backups
        schedule.every().day.at("01:00").do(
            lambda: asyncio.create_task(self.schedule_backup(BackupStrategy.DIFFERENTIAL))
        )
        
        logger.info("Backup schedules configured")
    
    async def run_scheduler(self):
        """Run the backup scheduler"""
        self.setup_schedules()
        logger.info("Backup scheduler started")
        
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute

if __name__ == "__main__":
    scheduler = BackupScheduler()
    asyncio.run(scheduler.run_scheduler())
