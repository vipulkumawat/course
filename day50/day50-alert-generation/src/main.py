"""Main application entry point."""
import asyncio
import sys
import uvicorn
from src.alert_engine.engine import AlertEngine
from src.web.app import app

async def run_alert_engine():
    """Run the alert engine standalone."""
    engine = AlertEngine()
    await engine.start()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        # Run web interface
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        # Run alert engine
        asyncio.run(run_alert_engine())

if __name__ == "__main__":
    main()

# Initialize logging
from src.utils.logging import setup_logging
setup_logging()
