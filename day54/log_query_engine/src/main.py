"""
Main application entry point
"""
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.query_api import app
from config.query_config import default_config

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=default_config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app

def main():
    """Main application entry point"""
    app = create_app()
    
    uvicorn.run(
        app,
        host=default_config.api_host,
        port=default_config.api_port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
