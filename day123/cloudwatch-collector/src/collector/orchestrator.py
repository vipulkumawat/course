"""Main orchestrator for CloudWatch log collection."""
import logging
import time
import threading
from typing import Dict, Any
import yaml

from .discovery import CloudWatchDiscovery
from .stream_processor import StreamProcessor
from ..pipeline.manager import PipelineManager
from ..utils.state_manager import StateManager


logger = logging.getLogger(__name__)


class CloudWatchCollector:
    """Main CloudWatch log collector orchestrator."""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        """Initialize collector."""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.state_manager = StateManager(self.config)
        self.discovery = CloudWatchDiscovery(self.config)
        self.stream_processor = StreamProcessor(self.config, self.state_manager)
        self.pipeline = PipelineManager(self.config)
        
        self.running = False
        self.threads = []
        
    def start(self):
        """Start the collector."""
        logger.info("Starting CloudWatch collector...")
        
        # Start pipeline
        self.pipeline.start()
        
        # Start collection loop
        self.running = True
        collection_thread = threading.Thread(
            target=self._collection_loop,
            name="collection-loop",
            daemon=True
        )
        collection_thread.start()
        self.threads.append(collection_thread)
        
        logger.info("CloudWatch collector started")
    
    def stop(self):
        """Stop the collector."""
        logger.info("Stopping CloudWatch collector...")
        
        self.running = False
        
        # Wait for threads
        for thread in self.threads:
            thread.join(timeout=5)
        
        # Stop pipeline
        self.pipeline.stop()
        
        logger.info("CloudWatch collector stopped")
    
    def _collection_loop(self):
        """Main collection loop."""
        last_discovery = 0
        
        while self.running:
            try:
                now = time.time()
                
                # Periodic discovery
                if now - last_discovery >= self.config['collector']['discovery_interval']:
                    logger.info("Running log group discovery...")
                    all_log_groups = self.discovery.discover_all()
                    logger.info(f"Discovered {sum(len(lg) for lg in all_log_groups.values())} log groups")
                    last_discovery = now
                else:
                    # Use cached discovery
                    all_log_groups = self.discovery.cache
                
                # Process each log group
                for key, log_groups in all_log_groups.items():
                    for log_group in log_groups:
                        try:
                            processed = self.stream_processor.process_log_group(
                                log_group,
                                self.pipeline.add_logs
                            )
                            
                            if processed > 0:
                                logger.debug(f"Processed {processed} events from {log_group.log_group_name}")
                        
                        except Exception as e:
                            logger.error(f"Error processing {log_group.log_group_name}: {e}")
                
                # Sleep before next poll
                time.sleep(self.config['collector']['polling_interval'])
                
            except Exception as e:
                logger.error(f"Collection loop error: {e}")
                time.sleep(5)
