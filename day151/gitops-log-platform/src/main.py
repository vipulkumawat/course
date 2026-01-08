"""
Main Application Entry Point
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.controller.gitops_controller import GitOpsController
from src.validator.deployment_validator import DeploymentValidator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitOpsApplication:
    def __init__(self, config_path: str = "config/gitops-config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.controller = None
        self.validator = None
        
    async def start(self):
        """Start the GitOps application"""
        logger.info("🚀 Starting GitOps Application")
        
        # Initialize controller
        self.controller = GitOpsController(self.config)
        await self.controller.initialize()
        
        # Initialize validator
        self.validator = DeploymentValidator(
            self.controller.k8s_apps_v1,
            self.controller.k8s_core_v1,
            self.config
        )
        
        # Start reconciliation loop
        await self.controller.reconciliation_loop()
        
    async def stop(self):
        """Stop the application"""
        if self.controller:
            await self.controller.stop()
        logger.info("👋 GitOps Application stopped")


async def main():
    app = GitOpsApplication()
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(app.stop())
        
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
