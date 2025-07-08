from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from .routers import search, auth, health
from middleware.rate_limiting import RateLimitMiddleware
from middleware.auth import AuthMiddleware

app = FastAPI(
    title="Log Search API",
    description="RESTful API for distributed log search with ranking",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(search.router, prefix="/api/v1/logs", tags=["search"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])

# Serve frontend
if os.path.exists("../frontend/build"):
    app.mount("/static", StaticFiles(directory="../frontend/build/static"), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend():
        with open("../frontend/build/index.html") as f:
            return f.read()

@app.get("/api/v1/")
async def root():
    return {
        "message": "Log Search API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }
