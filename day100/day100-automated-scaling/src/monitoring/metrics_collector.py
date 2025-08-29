import asyncio
import time
import psutil
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import json

@dataclass
class ComponentMetrics:
    component_id: str
    component_type: str
    timestamp: float
    cpu_percent: float
    memory_percent: float
    queue_depth: int = 0
    response_time_ms: float = 0.0
    throughput_per_sec: int = 0
    error_rate: float = 0.0
    instance_count: int = 1

class MetricsCollector:
    def __init__(self, config: Dict):
        self.config = config
        self.collection_interval = config.get('collection_interval', 30)
        self.components = {}
        self.running = False
        
    async def register_component(self, component_id: str, component_type: str, 
                                endpoint: str = None):
        """Register a component for monitoring"""
        self.components[component_id] = {
            'type': component_type,
            'endpoint': endpoint,
            'last_metrics': None
        }
        logging.info(f"Registered component {component_id} of type {component_type}")
    
    async def collect_system_metrics(self, component_id: str) -> ComponentMetrics:
        """Collect system-level metrics for a component"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Simulate component-specific metrics
        queue_depth = self._simulate_queue_depth(component_id)
        response_time = self._simulate_response_time(component_id)
        throughput = self._simulate_throughput(component_id)
        
        return ComponentMetrics(
            component_id=component_id,
            component_type=self.components[component_id]['type'],
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            queue_depth=queue_depth,
            response_time_ms=response_time,
            throughput_per_sec=throughput
        )
    
    def _simulate_queue_depth(self, component_id: str) -> int:
        """Simulate queue depth with realistic patterns"""
        import random
        base_depth = 100
        if 'processor' in component_id:
            # Processors have variable queue depths
            return base_depth + random.randint(0, 900)
        return base_depth + random.randint(0, 50)
    
    def _simulate_response_time(self, component_id: str) -> float:
        """Simulate response times with realistic patterns"""
        import random
        base_time = 50.0  # 50ms base
        if 'storage' in component_id:
            return base_time + random.uniform(0, 200)
        return base_time + random.uniform(0, 100)
    
    def _simulate_throughput(self, component_id: str) -> int:
        """Simulate throughput patterns"""
        import random
        if 'processor' in component_id:
            return random.randint(800, 1200)
        elif 'collector' in component_id:
            return random.randint(500, 800)
        return random.randint(200, 400)
    
    async def start_collection(self):
        """Start the metrics collection loop"""
        self.running = True
        logging.info("Starting metrics collection...")
        
        while self.running:
            try:
                for component_id in self.components:
                    metrics = await self.collect_system_metrics(component_id)
                    self.components[component_id]['last_metrics'] = metrics
                    logging.debug(f"Collected metrics for {component_id}: "
                                f"CPU={metrics.cpu_percent:.1f}%, "
                                f"Queue={metrics.queue_depth}")
                
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                logging.info("Metrics collection cancelled, shutting down...")
                break
            except Exception as e:
                logging.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(5)
        
        logging.info("Metrics collection stopped")
    
    def get_latest_metrics(self) -> Dict[str, ComponentMetrics]:
        """Get the latest metrics for all components"""
        return {cid: comp['last_metrics'] 
                for cid, comp in self.components.items() 
                if comp['last_metrics']}
    
    def stop_collection(self):
        """Stop the metrics collection"""
        logging.info("Stopping metrics collection...")
        self.running = False
        logging.info("Stopped metrics collection")
