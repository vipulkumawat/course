import asyncio
import json
import random
from datetime import datetime
from aiohttp import web

async def create_mock_health_endpoint(port: int, service_name: str):
    """Create a mock health endpoint for testing"""
    
    async def health_handler(request):
        # Simulate different health states
        rand = random.random()
        
        if rand < 0.7:  # 70% healthy
            status = "healthy"
        elif rand < 0.9:  # 20% warning
            status = "warning"
        else:  # 10% critical
            status = "critical"
            
        response_data = {
            "service": service_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "uptime": random.randint(3600, 86400),
            "metadata": {
                "instance_id": f"{service_name}-{port}",
                "region": "us-west-2"
            },
            "metrics": {
                "requests_per_second": random.uniform(10, 100),
                "error_rate": random.uniform(0, 0.05),
                "response_time_ms": random.uniform(50, 200)
            }
        }
        
        return web.json_response(response_data)
    
    app = web.Application()
    app.router.add_get('/health', health_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', port)
    await site.start()
    
    print(f"Mock service {service_name} running on http://localhost:{port}/health")
    return runner

async def start_mock_services():
    """Start all mock services"""
    services = [
        (8001, "log-collector"),
        (8002, "message-queue"),
        (8003, "processing-engine")
    ]
    
    runners = []
    for port, name in services:
        runner = await create_mock_health_endpoint(port, name)
        runners.append(runner)
    
    print("All mock services started. Press Ctrl+C to stop.")
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping mock services...")
        for runner in runners:
            await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(start_mock_services())
