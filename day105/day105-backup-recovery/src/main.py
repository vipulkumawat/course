import asyncio
import sys
import redis
from pathlib import Path
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent))

from scheduler.backup_scheduler import BackupScheduler
from dashboard.dashboard_api import app
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def start_redis():
    """Ensure Redis is running for coordination"""
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        redis_client.ping()
        logger.info("Redis connection successful")
        return True
    except:
        logger.warning("Redis not available, using in-memory coordination")
        return False

async def run_scheduler():
    """Run backup scheduler"""
    await start_redis()
    scheduler = BackupScheduler()
    await scheduler.run_scheduler()

async def run_dashboard():
    """Run dashboard API"""
    config = uvicorn.Config(app, host="0.0.0.0", port=8105)
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    if len(sys.argv) > 1 and sys.argv[1] == "dashboard":
        await run_dashboard()
    elif len(sys.argv) > 1 and sys.argv[1] == "scheduler":
        await run_scheduler()
    else:
        # Run both scheduler and dashboard
        tasks = [
            asyncio.create_task(run_scheduler()),
            asyncio.create_task(run_dashboard())
        ]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
