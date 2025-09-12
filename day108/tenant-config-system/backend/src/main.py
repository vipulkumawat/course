from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.config_api import router as config_router
from services.config_service import config_service
import asyncio
import uvicorn
import structlog

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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="Tenant Configuration Service",
    description="Multi-tenant configuration management system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await config_service.initialize()
    logger.info("Tenant Configuration Service started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if config_service.redis_client:
        await config_service.redis_client.close()
    logger.info("Tenant Configuration Service stopped")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        await config_service.redis_client.ping()
        return {"status": "healthy", "services": {"redis": "connected"}}
    except:
        return {"status": "unhealthy", "services": {"redis": "disconnected"}}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Tenant Configuration Service", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # Use structlog
    )
