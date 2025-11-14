import asyncio
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import aiohttp
import json
from queue import Queue, Empty
import logging

from .models import LogLevel, LogEntry, LogBatch
from .config import LogConfig

class DistributedLogger:
    """High-performance distributed logging client"""
    
    def __init__(self, config: LogConfig):
        self.config = config
        self.session = None
        self.batch_queue = Queue()
        self.current_batch = LogBatch(config.batch_size)
        self.running = False
        self.worker_thread = None
        self.last_batch_time = time.time()
        self.stats = {
            'logs_sent': 0,
            'logs_failed': 0,
            'batches_sent': 0,
            'errors': []
        }
        
        # Setup async event loop for worker thread
        self.loop = None
        
    async def _initialize_session(self):
        """Initialize HTTP session for sending logs"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config.connection_timeout_s)
            headers = {'Content-Type': 'application/json'}
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
    
    def start(self):
        """Start the logging client background worker"""
        if self.running:
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_thread, daemon=True)
        self.worker_thread.start()
        
    def stop(self):
        """Stop the logging client and flush remaining logs"""
        self.running = False
        
        # Send any remaining logs in current batch
        if not self.current_batch.is_empty():
            self.batch_queue.put(self.current_batch)
        
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
    
    def _worker_thread(self):
        """Background worker thread for processing log batches"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        async def worker():
            await self._initialize_session()
            
            while self.running:
                try:
                    # Check for batch timeout
                    current_time = time.time()
                    if (not self.current_batch.is_empty() and 
                        (current_time - self.last_batch_time) * 1000 > self.config.batch_timeout_ms):
                        self.batch_queue.put(self.current_batch)
                        self.current_batch = LogBatch(self.config.batch_size)
                        self.last_batch_time = current_time
                    
                    # Process queued batches
                    try:
                        batch = self.batch_queue.get(timeout=0.1)
                        await self._send_batch(batch)
                        self.batch_queue.task_done()
                    except Empty:
                        continue
                        
                except Exception as e:
                    self.stats['errors'].append(f"Worker error: {str(e)}")
                    await asyncio.sleep(1)
            
            # Cleanup
            if self.session:
                await self.session.close()
        
        self.loop.run_until_complete(worker())
    
    async def _send_batch(self, batch: LogBatch):
        """Send a batch of logs to the distributed logging system"""
        if batch.is_empty():
            return
            
        retry_count = 0
        while retry_count < self.config.retry_attempts:
            try:
                payload = batch.to_json()
                
                async with self.session.post(self.config.endpoint, data=payload) as response:
                    if response.status == 200:
                        self.stats['logs_sent'] += batch.size()
                        self.stats['batches_sent'] += 1
                        return
                    else:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )
                        
            except Exception as e:
                retry_count += 1
                if retry_count >= self.config.retry_attempts:
                    self.stats['logs_failed'] += batch.size()
                    self.stats['errors'].append(f"Failed to send batch: {str(e)}")
                    return
                
                # Exponential backoff
                await asyncio.sleep(self.config.retry_backoff_base * (2 ** retry_count))
    
    def _create_log_entry(self, level: LogLevel, message: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> LogEntry:
        """Create a standardized log entry"""
        return LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            message=message,
            service=self.config.service_name,
            component=self.config.component_name,
            metadata=metadata or {},
            request_id=str(uuid.uuid4()),
            session_id=getattr(threading.current_thread(), 'session_id', None),
            user_id=getattr(threading.current_thread(), 'user_id', None)
        )
    
    def _add_log_entry(self, entry: LogEntry):
        """Add log entry to current batch"""
        if not self.running:
            self.start()
        
        batch_full = self.current_batch.add_entry(entry)
        
        if batch_full:
            self.batch_queue.put(self.current_batch)
            self.current_batch = LogBatch(self.config.batch_size)
            self.last_batch_time = time.time()
    
    def debug(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log debug level message"""
        entry = self._create_log_entry(LogLevel.DEBUG, message, metadata)
        self._add_log_entry(entry)
    
    def info(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log info level message"""
        entry = self._create_log_entry(LogLevel.INFO, message, metadata)
        self._add_log_entry(entry)
    
    def warning(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log warning level message"""
        entry = self._create_log_entry(LogLevel.WARNING, message, metadata)
        self._add_log_entry(entry)
    
    def error(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log error level message"""
        entry = self._create_log_entry(LogLevel.ERROR, message, metadata)
        self._add_log_entry(entry)
    
    def critical(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log critical level message"""
        entry = self._create_log_entry(LogLevel.CRITICAL, message, metadata)
        self._add_log_entry(entry)
    
    def custom(self, event_type: str, data: Dict[str, Any]):
        """Log custom structured event"""
        metadata = {'event_type': event_type, **data}
        entry = self._create_log_entry(LogLevel.INFO, f"Custom event: {event_type}", metadata)
        self._add_log_entry(entry)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        return {
            **self.stats,
            'current_batch_size': self.current_batch.size(),
            'queue_size': self.batch_queue.qsize(),
            'running': self.running
        }
