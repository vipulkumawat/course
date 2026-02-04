#!/usr/bin/env python3
import asyncio
import signal
import yaml
import redis.asyncio as aioredis
import uvicorn
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.slo_evaluator import SLOEvaluator
from src.alerts.alert_manager import AlertManager
from src.api.sla_api import SLAAPI

class SLASystem:
    def __init__(self):
        with open('config/sla_config.yaml') as f:
            self.config = yaml.safe_load(f)
        self.redis = None
        self.tasks = []
    
    async def init(self):
        print("🚀 Initializing SLA Monitoring System...")
        cfg = self.config['redis']
        # Use environment variable if available (for Docker), otherwise use config
        redis_host = os.getenv('REDIS_HOST', cfg['host'])
        redis_port = cfg['port']
        redis_db = cfg['db']
        self.redis = await aioredis.from_url(f"redis://{redis_host}:{redis_port}/{redis_db}")
        
        self.metrics = MetricsCollector(self.redis)
        self.evaluator = SLOEvaluator(self.redis, self.metrics, self.config['sla_monitoring'])
        self.alerts = AlertManager(self.config['sla_monitoring'])
        self.api = SLAAPI(self.metrics, self.evaluator, self.alerts)
        print("✅ Components initialized")
    
    async def start(self):
        print("\n🎯 Starting monitoring...\n")
        self.tasks.append(asyncio.create_task(self.metrics.start_collection()))
        self.tasks.append(asyncio.create_task(self.evaluator.start_evaluation()))
        self.tasks.append(asyncio.create_task(self.alerts.start_monitoring(self.evaluator)))
        
        config = uvicorn.Config(self.api.app, host="0.0.0.0", port=8000, log_level="warning")
        server = uvicorn.Server(config)
        self.tasks.append(asyncio.create_task(server.serve()))
        
        print("✅ API: http://localhost:8000")
        print("📊 Dashboard: http://localhost:8000/api/slo/status")
        print("=" * 60)
    
    async def stop(self):
        print("\n⏹️  Shutting down...")
        await self.metrics.stop()
        await self.evaluator.stop()
        await self.alerts.stop()
        for t in self.tasks:
            t.cancel()
        if self.redis:
            await self.redis.close()

async def main():
    system = SLASystem()
    try:
        await system.init()
        await system.start()
        
        def handler(sig, frame):
            asyncio.create_task(system.stop())
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await system.stop()
        except Exception as e:
            print(f"Error in main loop: {e}")
            await system.stop()
    except Exception as e:
        print(f"Failed to start system: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
