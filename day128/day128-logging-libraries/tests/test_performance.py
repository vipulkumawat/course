#!/usr/bin/env python3

import asyncio
import time
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parent.parent))

from python_lib.logger import DistributedLogger
from python_lib.config import LogConfig

async def performance_test():
    """Test logging performance under load"""
    print("⚡ Running performance test...")
    
    config = LogConfig(
        endpoint="http://localhost:5000/api/logs",
        service_name="perf-test",
        batch_size=50,
        batch_timeout_ms=1000
    )
    
    logger = DistributedLogger(config)
    logger.start()
    
    # Test parameters
    num_logs = 1000
    start_time = time.time()
    
    # Send logs as fast as possible
    for i in range(num_logs):
        logger.info(f"Performance test message {i+1}", {
            'test_id': i+1,
            'batch_id': i // 50,
            'timestamp': time.time()
        })
    
    # Wait for all logs to be processed
    await asyncio.sleep(5)
    
    end_time = time.time()
    duration = end_time - start_time
    throughput = num_logs / duration
    
    stats = logger.get_stats()
    
    print(f"📊 Performance Results:")
    print(f"   Total logs: {num_logs}")
    print(f"   Duration: {duration:.2f} seconds")
    print(f"   Throughput: {throughput:.1f} logs/second")
    print(f"   Logs sent: {stats['logs_sent']}")
    print(f"   Success rate: {(stats['logs_sent'] / num_logs) * 100:.1f}%")
    
    logger.stop()
    
    # Performance criteria
    if throughput > 100:
        print("✅ Performance test PASSED")
        return True
    else:
        print("❌ Performance test FAILED")
        return False

if __name__ == "__main__":
    success = asyncio.run(performance_test())
    sys.exit(0 if success else 1)
