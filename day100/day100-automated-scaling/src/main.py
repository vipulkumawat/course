import asyncio
import logging
import signal
import sys
import uvicorn
from src.api.api_server import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting Automated Scaling System...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("📡 API endpoints at: http://localhost:8000/api/")
    print("💡 Press Ctrl+C to stop the system gracefully")
    
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000, 
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
