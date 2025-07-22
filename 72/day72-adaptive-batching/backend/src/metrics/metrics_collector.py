"""
MetricsCollector: Real-time system performance monitoring
"""

import asyncio
import psutil
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json

@dataclass
class SystemMetrics:
    timestamp: float
    cpu_usage: float
    memory_usage: float
    memory_available: float
    disk_io_read: float
    disk_io_write: float
    network_sent: float
    network_received: float
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ProcessingMetrics:
    timestamp: float
    batch_size: int
    processing_time: float
    throughput: float
    queue_depth: int
    error_rate: float
    
    def to_dict(self):
        return asdict(self)

class MetricsCollector:
    """Collects system and processing performance metrics"""
    
    def __init__(self, collection_interval: float = 1.0):
        self.collection_interval = collection_interval
        self.system_metrics_history: List[SystemMetrics] = []
        self.processing_metrics_history: List[ProcessingMetrics] = []
        self.max_history_size = 1000
        self._last_disk_io = None
        self._last_network_io = None
        self.running = False
        
    async def start_collection(self):
        """Start metrics collection"""
        self.running = True
        while self.running:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # Trim history
                if len(self.system_metrics_history) > self.max_history_size:
                    self.system_metrics_history.pop(0)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                print(f"Error collecting metrics: {e}")
                await asyncio.sleep(self.collection_interval)
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=None)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        memory_available = memory.available / (1024 * 1024)  # MB
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        if self._last_disk_io:
            disk_io_read = disk_io.read_bytes - self._last_disk_io.read_bytes
            disk_io_write = disk_io.write_bytes - self._last_disk_io.write_bytes
        else:
            disk_io_read = disk_io_write = 0
        self._last_disk_io = disk_io
        
        # Network I/O
        network_io = psutil.net_io_counters()
        if self._last_network_io:
            network_sent = network_io.bytes_sent - self._last_network_io.bytes_sent
            network_received = network_io.bytes_recv - self._last_network_io.bytes_recv
        else:
            network_sent = network_received = 0
        self._last_network_io = network_io
        
        return SystemMetrics(
            timestamp=time.time(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            memory_available=memory_available,
            disk_io_read=disk_io_read,
            disk_io_write=disk_io_write,
            network_sent=network_sent,
            network_received=network_received
        )
    
    def record_processing_metrics(self, batch_size: int, processing_time: float, 
                                queue_depth: int, error_count: int, total_processed: int):
        """Record processing performance metrics"""
        throughput = total_processed / processing_time if processing_time > 0 else 0
        error_rate = error_count / total_processed if total_processed > 0 else 0
        
        metrics = ProcessingMetrics(
            timestamp=time.time(),
            batch_size=batch_size,
            processing_time=processing_time,
            throughput=throughput,
            queue_depth=queue_depth,
            error_rate=error_rate
        )
        
        self.processing_metrics_history.append(metrics)
        
        # Trim history
        if len(self.processing_metrics_history) > self.max_history_size:
            self.processing_metrics_history.pop(0)
    
    def get_current_metrics(self) -> Dict:
        """Get current system state"""
        current_system = self.system_metrics_history[-1] if self.system_metrics_history else None
        current_processing = self.processing_metrics_history[-1] if self.processing_metrics_history else None
        
        return {
            "system": current_system.to_dict() if current_system else {},
            "processing": current_processing.to_dict() if current_processing else {},
            "history_size": len(self.system_metrics_history)
        }
    
    def get_metrics_window(self, seconds: int = 60) -> Dict:
        """Get metrics for the last N seconds"""
        current_time = time.time()
        cutoff_time = current_time - seconds
        
        recent_system = [m for m in self.system_metrics_history if m.timestamp >= cutoff_time]
        recent_processing = [m for m in self.processing_metrics_history if m.timestamp >= cutoff_time]
        
        return {
            "system_metrics": [m.to_dict() for m in recent_system],
            "processing_metrics": [m.to_dict() for m in recent_processing],
            "window_seconds": seconds
        }
    
    def calculate_performance_trends(self) -> Dict:
        """Calculate performance trends over time"""
        if len(self.processing_metrics_history) < 2:
            return {"trend": "insufficient_data"}
        
        recent_metrics = self.processing_metrics_history[-10:]  # Last 10 data points
        
        # Calculate throughput trend
        throughputs = [m.throughput for m in recent_metrics]
        throughput_trend = "increasing" if throughputs[-1] > throughputs[0] else "decreasing"
        
        # Calculate average batch size
        avg_batch_size = sum(m.batch_size for m in recent_metrics) / len(recent_metrics)
        
        # Calculate average processing time
        avg_processing_time = sum(m.processing_time for m in recent_metrics) / len(recent_metrics)
        
        return {
            "throughput_trend": throughput_trend,
            "avg_batch_size": avg_batch_size,
            "avg_processing_time": avg_processing_time,
            "current_throughput": throughputs[-1] if throughputs else 0
        }
