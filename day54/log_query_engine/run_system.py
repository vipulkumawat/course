"""
System runner for distributed query engine
"""
import sys
import os
import asyncio
import uvicorn

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import create_app

def main():
    """Run the distributed query engine"""
    print("🚀 Starting Distributed Log Query Engine...")
    print("📡 API Server: http://localhost:8000")
    print("🌐 Web Interface: http://localhost:8000")
    print("📊 Health Check: http://localhost:8000/api/health")
    
    app = create_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main()
