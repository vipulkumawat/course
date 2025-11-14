#!/usr/bin/env python3

import asyncio
import random
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_lib.logger import DistributedLogger
from python_lib.config import LogConfig

async def main():
    """Demo Python logging client"""
    print("🐍 Starting Python logging demo...")
    
    config = LogConfig.from_env()
    config.service_name = "python-demo-service"
    config.component_name = "demo-app"
    
    logger = DistributedLogger(config)
    logger.start()
    
    # Simulate application activity
    for i in range(100):
        # Random log levels and messages
        if random.random() < 0.1:
            logger.error(f"Simulated error in operation {i+1}", {
                'operation_id': i+1,
                'error_type': 'simulation',
                'source_language': 'python'
            })
        elif random.random() < 0.2:
            logger.warning(f"Warning: High memory usage in operation {i+1}", {
                'operation_id': i+1,
                'memory_usage_mb': random.randint(500, 1000),
                'source_language': 'python'
            })
        else:
            logger.info(f"Successfully completed operation {i+1}", {
                'operation_id': i+1,
                'duration_ms': random.randint(10, 500),
                'source_language': 'python'
            })
        
        # Random custom events
        if random.random() < 0.05:
            logger.custom('user_action', {
                'action': 'button_click',
                'user_id': f'user_{random.randint(1, 100)}',
                'source_language': 'python'
            })
        
        await asyncio.sleep(random.uniform(0.5, 2.0))
    
    print(f"📊 Final stats: {logger.get_stats()}")
    logger.stop()

if __name__ == "__main__":
    asyncio.run(main())
