import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.correlation_api import router as correlation_router
from correlation.engine import CorrelationEngine
from collectors.log_collector import LogCollector
import structlog

logger = structlog.get_logger()

# Global instances
correlation_engine = None
log_collector = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global correlation_engine, log_collector
    # Startup
    logger.info("Starting Correlation Analysis System")
    
    correlation_engine = CorrelationEngine()
    log_collector = LogCollector()
    
    # Set log collector reference in correlation engine
    correlation_engine.set_log_collector(log_collector)
    
    # Start log collection and correlation processing
    asyncio.create_task(log_collector.start_collection())
    asyncio.create_task(correlation_engine.start_processing())
    
    app.state.correlation_engine = correlation_engine
    app.state.log_collector = log_collector
    
    yield
    
    # Shutdown
    if correlation_engine:
        correlation_engine.stop_processing()
    if log_collector:
        log_collector.stop_collection()

app = FastAPI(title="Correlation Analysis System", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(correlation_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "correlation-analysis"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
