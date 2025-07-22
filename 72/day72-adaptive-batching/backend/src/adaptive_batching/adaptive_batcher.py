"""
AdaptiveBatcher: Main adaptive batching implementation
"""

import asyncio
import time
import random
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

from metrics.metrics_collector import MetricsCollector
from optimization.optimization_engine import OptimizationEngine

logger = logging.getLogger(__name__)

@dataclass
class LogMessage:
    id: str
    timestamp: float
    level: str
    source: str
    message: str
    metadata: Dict[str, Any]

class LogGenerator:
    """Simulates log message generation for testing"""
    
    def __init__(self):
        self.message_counter = 0
        self.sources = ["web-server", "database", "api-gateway", "auth-service", "payment-service"]
        self.levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        
    def generate_log(self) -> LogMessage:
        """Generate a realistic log message"""
        self.message_counter += 1
        
        return LogMessage(
            id=f"log_{self.message_counter}",
            timestamp=time.time(),
            level=random.choice(self.levels),
            source=random.choice(self.sources),
            message=f"Sample log message {self.message_counter}",
            metadata={
                "request_id": f"req_{random.randint(1000, 9999)}",
                "user_id": f"user_{random.randint(1, 1000)}",
                "processing_time_ms": random.randint(10, 500)
            }
        )

class AdaptiveBatcher:
    """Main adaptive batching system"""
    
    def __init__(self, metrics_collector: MetricsCollector, optimization_engine: OptimizationEngine):
        self.metrics_collector = metrics_collector
        self.optimization_engine = optimization_engine
        self.log_generator = LogGenerator()
        
        # Batching state
        self.current_batch: List[LogMessage] = []
        self.current_batch_size_target = 100
        self.processing_queue = asyncio.Queue()
        self.processed_count = 0
        self.error_count = 0
        
        # Control flags
        self.running = False
        self.simulation_active = False
        self.load_simulation_config = {}
        
        # Performance tracking
        self.batch_start_time = 0
        self.total_processing_time = 0
        self.total_batches_processed = 0
        
    async def start(self):
        """Start the adaptive batching system"""
        self.running = True
        logger.info("Starting adaptive batching system")
        
        # Start metrics collection
        asyncio.create_task(self.metrics_collector.start_collection())
        
        # Start main processing loops concurrently
        asyncio.create_task(self._batch_collection_loop())
        asyncio.create_task(self._batch_processing_loop())
        asyncio.create_task(self._optimization_loop())
        
        logger.info("All background tasks started")
    
    async def stop(self):
        """Stop the adaptive batching system"""
        self.running = False
        self.simulation_active = False
        self.metrics_collector.stop_collection()
        logger.info("Adaptive batching system stopped")
    
    async def _batch_collection_loop(self):
        """Main loop for collecting logs into batches"""
        while self.running:
            try:
                # Generate or collect logs (simulation for demo)
                if self.simulation_active:
                    await self._simulate_log_generation()
                
                # Check if batch is ready for processing
                if len(self.current_batch) >= self.current_batch_size_target:
                    await self._submit_batch_for_processing()
                
                await asyncio.sleep(0.1)  # 100ms collection interval
                
            except Exception as e:
                logger.error(f"Error in batch collection loop: {e}")
                await asyncio.sleep(1)
    
    async def _simulate_log_generation(self):
        """Simulate log generation based on load configuration"""
        config = self.load_simulation_config
        
        # Default simulation parameters
        messages_per_second = config.get("messages_per_second", 100)
        burst_probability = config.get("burst_probability", 0.1)
        burst_multiplier = config.get("burst_multiplier", 5)
        
        # Calculate messages to generate in this cycle
        base_messages = int(messages_per_second * 0.1)  # 100ms interval
        
        # Random burst generation
        if random.random() < burst_probability:
            messages_to_generate = base_messages * burst_multiplier
        else:
            messages_to_generate = base_messages
        
        # Add some randomness
        messages_to_generate = max(1, int(messages_to_generate * random.uniform(0.5, 1.5)))
        
        for _ in range(messages_to_generate):
            log_message = self.log_generator.generate_log()
            self.current_batch.append(log_message)
    
    async def _submit_batch_for_processing(self):
        """Submit current batch for processing"""
        if not self.current_batch:
            return
        
        batch_to_process = self.current_batch.copy()
        self.current_batch.clear()
        self.batch_start_time = time.time()
        
        await self.processing_queue.put(batch_to_process)
        logger.debug(f"Submitted batch of {len(batch_to_process)} messages for processing")
    
    async def _batch_processing_loop(self):
        """Main loop for processing batches"""
        while self.running:
            try:
                # Wait for batch to process
                batch = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=1.0
                )
                
                await self._process_batch(batch)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in batch processing loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_batch(self, batch: List[LogMessage]):
        """Process a batch of log messages"""
        batch_size = len(batch)
        start_time = time.time()
        
        try:
            # Simulate batch processing
            await self._simulate_batch_processing(batch)
            
            processing_time = time.time() - start_time
            self.processed_count += batch_size
            self.total_processing_time += processing_time
            self.total_batches_processed += 1
            
            # Record metrics
            queue_depth = self.processing_queue.qsize()
            self.metrics_collector.record_processing_metrics(
                batch_size=batch_size,
                processing_time=processing_time,
                queue_depth=queue_depth,
                error_count=self.error_count,
                total_processed=batch_size
            )
            
            logger.debug(f"Processed batch of {batch_size} messages in {processing_time:.3f}s")
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing batch: {e}")
    
    async def _simulate_batch_processing(self, batch: List[LogMessage]):
        """Simulate realistic batch processing with variable complexity"""
        batch_size = len(batch)
        
        # Simulate processing complexity based on batch size
        base_processing_time = 0.01  # 10ms base
        size_factor = batch_size / 1000  # Complexity increases with size
        processing_time = base_processing_time + (size_factor * 0.1)
        
        # Add some randomness to simulate real-world variability
        processing_time *= random.uniform(0.8, 1.2)
        
        # Simulate memory pressure for large batches
        if batch_size > 2000:
            processing_time *= 1.5  # 50% slower for large batches
        
        await asyncio.sleep(processing_time)
        
        # Simulate occasional processing errors
        if random.random() < 0.01:  # 1% error rate
            raise Exception("Simulated processing error")
    
    async def _optimization_loop(self):
        """Main optimization loop"""
        while self.running:
            try:
                await asyncio.sleep(5)  # Optimize every 5 seconds
                
                # Get current metrics
                current_metrics = self.metrics_collector.get_current_metrics()
                
                if current_metrics["processing"]:  # Only optimize if we have data
                    # Calculate optimal batch size
                    new_batch_size, decision = self.optimization_engine.calculate_optimal_batch_size(current_metrics)
                    
                    # Apply new batch size
                    old_batch_size = self.current_batch_size_target
                    self.current_batch_size_target = new_batch_size
                    
                    logger.info(f"Batch size adjusted: {old_batch_size} → {new_batch_size} "
                              f"(throughput: {current_metrics['processing'].get('throughput', 0):.1f} msg/s)")
                
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(10)  # Longer delay on error
    
    async def simulate_load(self, load_config: Dict):
        """Start load simulation with given configuration"""
        self.load_simulation_config = load_config
        self.simulation_active = True
        logger.info(f"Started load simulation: {load_config}")
    
    def stop_simulation(self):
        """Stop load simulation"""
        self.simulation_active = False
        self.load_simulation_config = {}
        logger.info("Stopped load simulation")
    
    def get_current_metrics(self) -> Dict:
        """Get current system metrics and status"""
        metrics = self.metrics_collector.get_current_metrics()
        optimization_status = self.optimization_engine.get_optimization_status()
        
        # Add batching-specific metrics
        metrics["batching"] = {
            "current_batch_size_target": self.current_batch_size_target,
            "current_batch_count": len(self.current_batch),
            "queue_depth": self.processing_queue.qsize(),
            "total_processed": self.processed_count,
            "total_errors": self.error_count,
            "total_batches": self.total_batches_processed,
            "avg_processing_time": (
                self.total_processing_time / self.total_batches_processed
                if self.total_batches_processed > 0 else 0
            ),
            "simulation_active": self.simulation_active,
            "simulation_config": self.load_simulation_config
        }
        
        metrics["optimization"] = optimization_status
        
        return metrics
    
    def reset_statistics(self):
        """Reset all statistics (useful for testing)"""
        self.processed_count = 0
        self.error_count = 0
        self.total_processing_time = 0
        self.total_batches_processed = 0
        self.optimization_engine.reset_optimization()
        logger.info("Statistics reset")
