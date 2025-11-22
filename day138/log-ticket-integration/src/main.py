#!/usr/bin/env python3
"""
Day 138: JIRA/ServiceNow Ticket Creation System
Main FastAPI application entry point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import structlog
import uvicorn
import os

from src.api.tickets import router as tickets_router
from src.api.events import router as events_router
from src.api.dashboard import router as dashboard_router
from src.services.event_processor import EventProcessor
from src.services.ticket_service import TicketService

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
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global services
event_processor: EventProcessor = None
ticket_service: TicketService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global event_processor, ticket_service

    logger.info("Starting JIRA/ServiceNow Ticket Creation System")

    # Initialize services
    ticket_service = TicketService()
    await ticket_service.initialize()

    event_processor = EventProcessor(ticket_service)
    await event_processor.start()

    logger.info("System initialized successfully")

    yield

    # Cleanup
    await event_processor.stop()
    await ticket_service.close()
    logger.info("System shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Log Ticket Integration System",
    description="Automatic JIRA/ServiceNow ticket creation from log events",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tickets_router, prefix="/api/tickets", tags=["tickets"])
app.include_router(events_router, prefix="/api/events", tags=["events"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])

# Serve frontend static files (JS, CSS, etc.)
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

# Path to frontend index.html
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build")
INDEX_HTML = os.path.join(FRONTEND_BUILD_DIR, "index.html")


@app.get("/")
async def root():
    """Serve frontend HTML"""
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    return HTMLResponse("""
    <html>
        <head><title>Service Info</title></head>
        <body>
            <h1>Log Ticket Integration System</h1>
            <p>Frontend not found. Please build the frontend first.</p>
            <pre>{"service":"Log Ticket Integration System","day":138,"module":"Integration and Ecosystem","status":"active"}</pre>
        </body>
    </html>
    """)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "event_processor": event_processor.is_running() if event_processor else False,
        "ticket_service": ticket_service.is_connected() if ticket_service else False,
    }


# Catch-all route for React Router (must be last)
@app.get("/{full_path:path}")
async def serve_frontend(request: Request, full_path: str):
    """Serve frontend for all non-API routes (React Router)"""
    # Don't serve frontend for API routes
    if full_path.startswith("api/"):
        return {"error": "Not found"}
    
    # Don't serve frontend for static files
    if full_path.startswith("static/"):
        return {"error": "Not found"}
    
    # Serve index.html for all other routes (React Router will handle routing)
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    return {"error": "Frontend not found"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "event_processor": event_processor.is_running() if event_processor else False,
        "ticket_service": ticket_service.is_connected() if ticket_service else False,
    }


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True, log_config=None)
