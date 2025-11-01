"""Main entry point for CloudWatch collector."""
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
import signal
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collector.orchestrator import CloudWatchCollector
from src.api.dashboard import start_dashboard
from prometheus_client import start_http_server


# Setup logging
def setup_logging():
    """Configure logging."""
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler('logs/cloudwatch-collector.log', maxBytes=10485760, backupCount=5),
            logging.StreamHandler()
        ]
    )


def main():
    """Main function."""
    # Load environment
    load_dotenv()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("AWS CloudWatch Log Collector - Day 123")
    logger.info("=" * 60)
    
    # Initialize collector
    collector = CloudWatchCollector()
    
    # Start Prometheus metrics server
    prometheus_port = int(os.getenv('PROMETHEUS_PORT', 8000))
    start_http_server(prometheus_port)
    logger.info(f"Prometheus metrics: http://localhost:{prometheus_port}/metrics")
    
    # Start collector
    collector.start()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        collector.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start dashboard
    dashboard_port = int(os.getenv('DASHBOARD_PORT', 5000))
    logger.info(f"Dashboard: http://localhost:{dashboard_port}")
    start_dashboard(collector, port=dashboard_port)


if __name__ == '__main__':
    main()
