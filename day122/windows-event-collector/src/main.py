"""Windows Event Log Agent - Main Application"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Import our modules
from agent.core.event_agent import WindowsEventAgent
from transport.event_shipper import EventShipper
from web.dashboard_app import app, set_active_agent, broadcast_event
import uvicorn
from monitoring.metrics import start_metrics_server

class WindowsEventLogService:
    """Main service orchestrating all components"""
    
    def __init__(self):
        self.agent = None
        self.shipper = None
        self.running = False
        
    async def initialize(self):
        """Initialize all service components"""
        logger.info("Initializing Windows Event Log Service")
        
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Initialize transport layer
        self.shipper = EventShipper()
        await self.shipper.initialize()
        
        # Initialize agent with shipper callback
        self.agent = WindowsEventAgent(event_callback=self.shipper.ship_event)
        await self.agent.initialize()
        
        # Set agent for dashboard
        set_active_agent(self.agent)
        
        # Start metrics endpoint (with simple port fallback)
        from config.agent_config import config as agent_config
        metrics_started = False
        for port in (agent_config.metrics_port, agent_config.metrics_port + 1, agent_config.metrics_port + 2):
            if metrics_started:
                break
            try:
                start_metrics_server(port)
                logger.info(f"Metrics server started on :{port} at /metrics")
                metrics_started = True
            except Exception as metrics_error:
                logger.warning(f"Failed to start metrics server on :{port}: {metrics_error}")

        logger.info("Service initialization complete")
        
    async def start(self):
        """Start the service"""
        logger.info("Starting Windows Event Log Service")
        self.running = True
        try:
            await broadcast_event({'action': 'Collection started', 'timestamp': datetime.now().isoformat()})
        except Exception:
            pass
        
        # Start event collection
        collection_task = asyncio.create_task(self.agent.start_collection())
        
        # Start web dashboard
        config = uvicorn.Config(
            app, 
            host="0.0.0.0", 
            port=8080,
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)
        server_task = asyncio.create_task(server.serve())
        
        logger.info("🌐 Dashboard available at: http://localhost:8080")
        
        try:
            # Run both tasks
            await asyncio.gather(collection_task, server_task)
        except Exception as e:
            logger.error(f"Service error: {e}")
        finally:
            await self.stop()
            
    async def stop(self):
        """Stop the service gracefully"""
        logger.info("Stopping Windows Event Log Service")
        self.running = False
        try:
            await broadcast_event({'action': 'Collection stopped', 'timestamp': datetime.now().isoformat()})
        except Exception:
            pass
        
        if self.agent:
            await self.agent.stop_collection()
            
        if self.shipper:
            await self.shipper.close()
            
        logger.info("Service stopped")

# Global service instance
service = WindowsEventLogService()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    asyncio.create_task(service.stop())

async def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.initialize()
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        await service.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await service.stop()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted")
        sys.exit(0)
