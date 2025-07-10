#!/usr/bin/env python3
"""
Day 60: Multi-Region Log Replication System - Dashboard
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import asyncio
import json
from datetime import datetime
import structlog
import os

# Configure logging
logger = structlog.get_logger()

app = FastAPI(
    title="Day 60: Log Replication Dashboard",
    description="Web dashboard for monitoring multi-region log replication",
    version="1.0.0"
)

# Mount static files if directory exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Region configuration
REGIONS = [
    {"name": "us-east-1", "url": "http://localhost:8000", "color": "#3B82F6"},
    {"name": "us-west-2", "url": "http://localhost:8001", "color": "#10B981"},
    {"name": "eu-west-1", "url": "http://localhost:8002", "color": "#F59E0B"}
]

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    try:
        with open("templates/dashboard.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard template not found</h1>")

@app.get("/api/status")
async def get_status():
    """Get status of all regions"""
    status_data = []
    
    async with aiohttp.ClientSession() as session:
        for region in REGIONS:
            try:
                async with session.get(f"{region['url']}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        status_data.append({
                            "region": region["name"],
                            "status": "healthy",
                            "log_count": data.get("log_count", 0),
                            "timestamp": data.get("timestamp", ""),
                            "color": region["color"]
                        })
                    else:
                        status_data.append({
                            "region": region["name"],
                            "status": "unhealthy",
                            "log_count": 0,
                            "timestamp": "",
                            "color": region["color"]
                        })
            except Exception as e:
                logger.error("Failed to check region", region=region["name"], error=str(e))
                status_data.append({
                    "region": region["name"],
                    "status": "error",
                    "log_count": 0,
                    "timestamp": "",
                    "color": region["color"]
                })
    
    return {"regions": status_data}

@app.get("/api/logs")
async def get_logs(region: str = None, limit: int = 50):
    """Get logs from all regions"""
    all_logs = []
    
    async with aiohttp.ClientSession() as session:
        for region_config in REGIONS:
            try:
                url = f"{region_config['url']}/logs"
                if region:
                    url += f"?region={region}"
                if limit:
                    url += f"{'&' if '?' in url else '?'}limit={limit}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for log in data.get("logs", []):
                            log["source_region"] = region_config["name"]
                            log["color"] = region_config["color"]
                            all_logs.append(log)
            except Exception as e:
                logger.error("Failed to fetch logs", region=region_config["name"], error=str(e))
    
    # Sort by timestamp
    all_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {"logs": all_logs[:limit]}

@app.post("/api/logs")
async def add_log(request: Request):
    """Add a log entry to a specific region"""
    data = await request.json()
    
    region_name = data.get("region", "us-east-1")
    region_url = next((r["url"] for r in REGIONS if r["name"] == region_name), REGIONS[0]["url"])
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{region_url}/logs", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"status": "success", "log_id": result.get("log_id")}
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
        except Exception as e:
            logger.error("Failed to add log", region=region_name, error=str(e))
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("DASHBOARD_PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port) 