from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from src.api import routes, oauth_routes
from config.settings import settings
import uvicorn

app = FastAPI(
    title="BI Integration API",
    description="Business Intelligence tool integration for distributed log processing",
    version=settings.API_VERSION
)

# CORS middleware for BI tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/exports", StaticFiles(directory="exports"), name="exports")

# Include routers
app.include_router(oauth_routes.router, prefix="/oauth", tags=["authentication"])
app.include_router(routes.router, prefix=f"/api/{settings.API_VERSION}", tags=["metrics"])

@app.get("/", response_class=HTMLResponse)
async def root():
    """Dashboard landing page - redirects to dashboard"""
    from fastapi.responses import FileResponse
    from pathlib import Path
    dashboard_path = Path("static") / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    # Fallback if dashboard.html doesn't exist
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>BI Integration Dashboard</title>
        <meta http-equiv="refresh" content="0; url=/dashboard">
    </head>
    <body>
        <p>Redirecting to dashboard... <a href="/dashboard">Click here</a></p>
    </body>
    </html>
    """

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page"""
    from fastapi.responses import FileResponse
    from pathlib import Path
    dashboard_path = Path("static") / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return HTMLResponse("Dashboard not found", status_code=404)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.API_VERSION}

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
