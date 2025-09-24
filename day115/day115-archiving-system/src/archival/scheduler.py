import asyncio
import schedule
import structlog
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
import json
import os

from src.archival.manager import ArchivalManager, LogEntry

logger = structlog.get_logger()

class ArchivalScheduler:
    def __init__(self, manager: ArchivalManager, config):
        self.manager = manager
        self.config = config
        self.running = False
        
    async def start_scheduler(self):
        """Start the archival scheduler"""
        self.running = True
        
        # Schedule archival jobs every 6 hours
        schedule.every(self.config.schedule_interval_hours).hours.do(
            lambda: asyncio.create_task(self.run_archival_cycle())
        )
        
        logger.info("Archival scheduler started", 
                   interval_hours=self.config.schedule_interval_hours)
        
        while self.running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
    
    async def stop_scheduler(self):
        """Stop the archival scheduler"""
        self.running = False
        logger.info("Archival scheduler stopped")
    
    async def run_archival_cycle(self):
        """Run complete archival cycle"""
        try:
            logger.info("Starting archival cycle")
            
            # Find logs eligible for archival
            eligible_logs = await self._find_eligible_logs()
            
            if not eligible_logs:
                logger.info("No logs eligible for archival")
                return
            
            # Create archival jobs in batches
            batches = self._create_batches(eligible_logs, self.config.batch_size)
            
            for batch in batches:
                job = await self.manager.create_archival_job(batch)
                success = await self.manager.process_archival_job(job)
                
                if success:
                    # Mark original logs as archived
                    await self._mark_logs_archived(batch)
            
            logger.info("Archival cycle completed", 
                       total_logs=len(eligible_logs),
                       batches=len(batches))
                       
        except Exception as e:
            logger.error("Archival cycle failed", error=str(e))
    
    async def _find_eligible_logs(self) -> List[LogEntry]:
        """Find logs eligible for archival based on policies"""
        eligible_logs = []
        logs_dir = Path("logs")
        
        if not logs_dir.exists():
            return eligible_logs
        
        cutoff_date = datetime.now() - timedelta(days=7)  # Archive logs older than 7 days
        
        for log_file in logs_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                # Parse log file and create LogEntry objects
                entries = await self._parse_log_file(log_file)
                eligible_logs.extend(entries)
        
        return eligible_logs
    
    async def _parse_log_file(self, file_path: Path) -> List[LogEntry]:
        """Parse log file into LogEntry objects"""
        entries = []
        
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f):
                    if line.strip():
                        try:
                            log_data = json.loads(line)
                            entry = LogEntry(
                                id=f"{file_path.stem}_{line_num}",
                                timestamp=datetime.fromisoformat(log_data.get('timestamp', datetime.now().isoformat())),
                                level=log_data.get('level', 'INFO'),
                                service=log_data.get('service', 'unknown'),
                                message=log_data.get('message', ''),
                                metadata=log_data.get('metadata', {}),
                                size_bytes=len(line.encode()),
                                file_path=str(file_path)
                            )
                            entries.append(entry)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error("Failed to parse log file", file_path=str(file_path), error=str(e))
        
        return entries
    
    def _create_batches(self, logs: List[LogEntry], batch_size: int) -> List[List[LogEntry]]:
        """Create batches of logs for processing"""
        batches = []
        for i in range(0, len(logs), batch_size):
            batches.append(logs[i:i + batch_size])
        return batches
    
    async def _mark_logs_archived(self, entries: List[LogEntry]):
        """Mark original log files as archived"""
        archived_files = set(entry.file_path for entry in entries)
        
        for file_path in archived_files:
            archived_path = Path(file_path).parent / "archived" / Path(file_path).name
            archived_path.parent.mkdir(exist_ok=True)
            
            try:
                os.rename(file_path, archived_path)
                logger.info("Moved log file to archived", 
                           original=file_path, archived=str(archived_path))
            except Exception as e:
                logger.error("Failed to move log file", file_path=file_path, error=str(e))
