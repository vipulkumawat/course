#!/usr/bin/env python3
import sys
import asyncio
from src.api.api_server import app
import uvicorn
from config.config import config

def main():
    print("🔒 Starting IOC Scanner System")
    print("="*50)
    
    print(f"API Server: http://{config.api_host}:{config.api_port}")
    print(f"Dashboard: http://localhost:3000")
    print(f"Redis: {config.redis_host}:{config.redis_port}")
    
    uvicorn.run(app, host=config.api_host, port=config.api_port)

if __name__ == "__main__":
    main()
