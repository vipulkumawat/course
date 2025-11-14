#!/usr/bin/env python3

import asyncio
import json
import sys
import time
import threading
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_lib.logger import DistributedLogger
from python_lib.config import LogConfig
from python_lib.models import LogLevel

async def test_python_client():
    """Test Python logging client"""
    print("🐍 Testing Python client...")
    
    config = LogConfig(
        endpoint="http://localhost:5000/api/logs",
        service_name="test-service",
        component_name="integration-test",
        batch_size=5,
        batch_timeout_ms=2000
    )
    
    logger = DistributedLogger(config)
    logger.start()
    
    # Send test logs
    for i in range(10):
        logger.info(f"Python test message {i+1}", {
            'test_id': i+1,
            'source_language': 'python'
        })
        
        if i % 3 == 0:
            logger.error(f"Python test error {i+1}", {
                'error_code': f'E{i+1}',
                'source_language': 'python'
            })
    
    # Wait for logs to be sent
    await asyncio.sleep(3)
    
    stats = logger.get_stats()
    print(f"   ✅ Python stats: {stats}")
    
    logger.stop()
    return stats['logs_sent'] > 0

def test_nodejs_client():
    """Test Node.js client by running the example"""
    print("🟨 Testing Node.js client...")
    
    import subprocess
    import os
    
    # Create test script
    test_script = """
const { DistributedLogger } = require('./nodejs-lib');

const logger = new DistributedLogger({
    endpoint: 'http://localhost:5000/api/logs',
    serviceName: 'test-service',
    componentName: 'nodejs-integration-test',
    batchSize: 5,
    batchTimeoutMs: 2000
});

logger.start();

// Send test logs
for (let i = 0; i < 10; i++) {
    logger.info(`Node.js test message ${i+1}`, {
        test_id: i+1,
        source_language: 'nodejs'
    });
    
    if (i % 3 === 0) {
        logger.error(`Node.js test error ${i+1}`, {
            error_code: `E${i+1}`,
            source_language: 'nodejs'
        });
    }
}

setTimeout(() => {
    const stats = logger.getStats();
    console.log('Node.js stats:', JSON.stringify(stats));
    logger.stop();
    process.exit(0);
}, 3000);
"""
    
    with open('test_nodejs.js', 'w') as f:
        f.write(test_script)
    
    try:
        result = subprocess.run(['node', 'test_nodejs.js'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and 'logs_sent' in result.stdout:
            print("   ✅ Node.js client test passed")
            return True
        else:
            print(f"   ❌ Node.js test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Node.js test error: {e}")
        return False
    finally:
        if os.path.exists('test_nodejs.js'):
            os.remove('test_nodejs.js')

async def test_dashboard_api():
    """Test dashboard API endpoints"""
    print("🌐 Testing dashboard API...")
    
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test stats endpoint
            async with session.get('http://localhost:5000/api/stats') as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"   ✅ Stats API working: {stats.get('total_logs', 0)} total logs")
                    return True
                else:
                    print(f"   ❌ Stats API failed: {response.status}")
                    return False
    except Exception as e:
        print(f"   ❌ Dashboard API test error: {e}")
        return False

async def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting integration tests...\n")
    
    results = []
    
    # Test Python client
    try:
        result = await test_python_client()
        results.append(('Python Client', result))
    except Exception as e:
        print(f"   ❌ Python test error: {e}")
        results.append(('Python Client', False))
    
    # Test Node.js client
    try:
        result = test_nodejs_client()
        results.append(('Node.js Client', result))
    except Exception as e:
        print(f"   ❌ Node.js test error: {e}")
        results.append(('Node.js Client', False))
    
    # Test dashboard API
    try:
        result = await test_dashboard_api()
        results.append(('Dashboard API', result))
    except Exception as e:
        print(f"   ❌ Dashboard API test error: {e}")
        results.append(('Dashboard API', False))
    
    # Print results
    print("\n📊 Integration Test Results:")
    print("=" * 40)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All integration tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check dashboard logs.")
        return False

if __name__ == "__main__":
    print("Integration Tests for Multi-Language Logging Libraries")
    print("Make sure the dashboard is running at http://localhost:5000")
    print("=" * 60)
    
    # Wait a moment for dashboard to be ready
    print("⏳ Waiting for dashboard to be ready...")
    time.sleep(2)
    
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)
