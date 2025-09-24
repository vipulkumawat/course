import asyncio
import uvicorn
import structlog
from pathlib import Path

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.archival.manager import ArchivalManager
from src.archival.scheduler import ArchivalScheduler
from src.storage.managers import StorageTierManager
from src.monitoring.dashboard import ArchivalDashboard
from config.archival_config import config

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def main():
    """Main application entry point"""
    logger.info("Starting Historical Data Archiving System")
    
    # Initialize components
    archival_manager = ArchivalManager(config)
    storage_manager = StorageTierManager(config)
    scheduler = ArchivalScheduler(archival_manager, config)
    dashboard = ArchivalDashboard(archival_manager, storage_manager)
    
    # Create sample log files for demonstration
    await create_sample_logs()
    
    # Start scheduler in background
    scheduler_task = asyncio.create_task(scheduler.start_scheduler())
    
    # Start web server
    web_config = uvicorn.Config(
        app=dashboard.app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
    server = uvicorn.Server(web_config)
    
    logger.info("Dashboard available at http://localhost:8001")
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await scheduler.stop_scheduler()
        scheduler_task.cancel()

async def create_sample_logs():
    """Create sample log files for demonstration"""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    sample_logs = [
        '{"timestamp": "2025-05-01T10:00:00Z", "level": "INFO", "service": "api", "message": "Request processed", "metadata": {"duration_ms": 45}}',
        '{"timestamp": "2025-05-01T10:01:00Z", "level": "ERROR", "service": "database", "message": "Connection timeout", "metadata": {"retry_count": 3}}',
        '{"timestamp": "2025-05-01T10:02:00Z", "level": "WARN", "service": "auth", "message": "Rate limit exceeded", "metadata": {"user_id": "12345"}}',
        '{"timestamp": "2025-05-01T10:03:00Z", "level": "INFO", "service": "cache", "message": "Cache hit", "metadata": {"key": "user_profile_12345"}}',
        '{"timestamp": "2025-05-01T10:04:00Z", "level": "DEBUG", "service": "scheduler", "message": "Job scheduled", "metadata": {"job_id": "arch_001"}}'
    ]
    
    # Create multiple log files with different timestamps
    for i in range(3):
        log_file = logs_dir / f"app_{i}.log"
        with open(log_file, 'w') as f:
            for log in sample_logs:
                f.write(log + '\n')
        
        # Set file timestamp to 8 days ago to make it eligible for archival
        import os
        import time
        old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days ago
        os.utime(log_file, (old_time, old_time))
    
    logger.info("Sample log files created", count=3)

if __name__ == "__main__":
    asyncio.run(main())
