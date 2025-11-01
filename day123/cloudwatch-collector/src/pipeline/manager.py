"""Pipeline manager for processing and forwarding logs."""
import logging
import queue
import threading
import time
from typing import List, Dict, Any
import requests

from ..models.log_entry import CloudWatchLogEntry
from prometheus_client import Counter, Histogram, Gauge


logger = logging.getLogger(__name__)

# Metrics
logs_processed = Counter('cloudwatch_logs_processed_total', 'Total logs processed')
logs_forwarded = Counter('cloudwatch_logs_forwarded_total', 'Total logs forwarded')
logs_dropped = Counter('cloudwatch_logs_dropped_total', 'Total logs dropped')
processing_duration = Histogram('cloudwatch_processing_duration_seconds', 'Log processing duration')
buffer_size_gauge = Gauge('cloudwatch_buffer_size', 'Current buffer size')


class PipelineManager:
    """Manages log processing and forwarding pipeline."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize pipeline manager."""
        self.config = config
        self.buffer = queue.Queue(maxsize=config['pipeline']['buffer_size'])
        self.running = False
        self.workers = []
        
        # Circuit breaker state
        self.circuit_state = 'closed'
        self.failure_count = 0
        self.last_failure_time = 0
        
    def start(self):
        """Start pipeline workers."""
        self.running = True
        
        # Start worker threads
        num_workers = self.config['pipeline']['worker_threads']
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"pipeline-worker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {num_workers} pipeline workers")
    
    def stop(self):
        """Stop pipeline workers."""
        self.running = False
        
        # Wait for workers
        for worker in self.workers:
            worker.join(timeout=5)
        
        logger.info("Stopped pipeline workers")
    
    def add_logs(self, logs: List[CloudWatchLogEntry]):
        """Add logs to processing buffer."""
        for log in logs:
            try:
                self.buffer.put(log, block=False)
                buffer_size_gauge.set(self.buffer.qsize())
            except queue.Full:
                logger.warning("Buffer full, dropping log")
                logs_dropped.inc()
    
    def _worker_loop(self):
        """Worker thread main loop."""
        batch = []
        last_forward = time.time()
        
        while self.running:
            try:
                # Get log with timeout
                try:
                    log = self.buffer.get(timeout=1.0)
                    batch.append(log)
                    logs_processed.inc()
                except queue.Empty:
                    pass
                
                # Forward batch if size or time threshold reached
                now = time.time()
                should_forward = (
                    len(batch) >= self.config['forwarding']['batch_size'] or
                    (batch and now - last_forward >= self.config['collector']['max_batch_wait'])
                )
                
                if should_forward:
                    self._forward_batch(batch)
                    batch = []
                    last_forward = now
                
                buffer_size_gauge.set(self.buffer.qsize())
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(1)
        
        # Forward remaining logs
        if batch:
            self._forward_batch(batch)
    
    def _forward_batch(self, batch: List[CloudWatchLogEntry]):
        """Forward batch of logs to downstream system."""
        if not self.config['forwarding']['enabled']:
            return
        
        if self.circuit_state == 'open':
            # Check if we should try half-open
            if time.time() - self.last_failure_time > self.config['pipeline']['circuit_breaker']['half_open_timeout']:
                self.circuit_state = 'half-open'
            else:
                logger.warning(f"Circuit breaker open, dropping {len(batch)} logs")
                logs_dropped.inc(len(batch))
                return
        
        try:
            with processing_duration.time():
                # Convert to JSON
                payload = [log.to_dict() for log in batch]
                
                # Forward to endpoint
                response = requests.post(
                    self.config['forwarding']['endpoint'],
                    json={'logs': payload},
                    timeout=self.config['forwarding']['timeout']
                )
                
                response.raise_for_status()
                logs_forwarded.inc(len(batch))
                
                # Reset circuit breaker on success
                if self.circuit_state == 'half-open':
                    self.circuit_state = 'closed'
                    self.failure_count = 0
                    logger.info("Circuit breaker closed")
                
        except Exception as e:
            logger.error(f"Failed to forward batch: {e}")
            self._handle_forward_failure(len(batch))
    
    def _handle_forward_failure(self, count: int):
        """Handle forwarding failure."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        threshold = self.config['pipeline']['circuit_breaker']['failure_threshold']
        
        if self.failure_count >= threshold:
            self.circuit_state = 'open'
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")
        
        logs_dropped.inc(count)
