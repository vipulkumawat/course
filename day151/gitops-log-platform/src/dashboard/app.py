"""
GitOps Dashboard
Real-time web interface for monitoring GitOps deployments
"""
import asyncio
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="GitOps Dashboard")

# Mount static files and templates
import os
from pathlib import Path

# Get the directory where this script is located
BASE_DIR = Path(__file__).parent.parent.parent
TEMPLATE_DIR = BASE_DIR / "web" / "templates"

# Ensure template directory exists
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Global state (in production, use Redis or similar)
gitops_status = {
    'running': False,
    'last_sync': None,
    'deployments': [],
    'metrics': {
        'total_deployments': 0,
        'successful_deployments': 0,
        'failed_deployments': 0
    }
}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "status": gitops_status
    })


@app.get("/api/status")
async def get_status():
    """Get current GitOps controller status"""
    return gitops_status


@app.get("/api/deployments")
async def get_deployments():
    """Get deployment history"""
    return {
        'deployments': gitops_status['deployments'],
        'total': len(gitops_status['deployments'])
    }


@app.post("/api/sync")
async def trigger_sync():
    """Manually trigger a sync"""
    from datetime import datetime
    import random
    
    # Simulate a deployment for demo purposes
    deployment = {
        'timestamp': datetime.now().isoformat(),
        'commit': f"{random.randint(10000000, 99999999):08x}",
        'changes': random.randint(1, 5),
        'success': True
    }
    
    gitops_status['deployments'].append(deployment)
    gitops_status['metrics']['total_deployments'] += 1
    gitops_status['metrics']['successful_deployments'] += 1
    gitops_status['running'] = True
    gitops_status['last_sync'] = datetime.now().isoformat()
    
    # Keep last 50 deployments
    if len(gitops_status['deployments']) > 50:
        gitops_status['deployments'] = gitops_status['deployments'][-50:]
    
    return {'status': 'sync_triggered', 'message': 'Manual sync initiated', 'deployment': deployment}


@app.post("/api/rollback/{deployment_name}")
async def trigger_rollback(deployment_name: str):
    """Trigger deployment rollback"""
    from datetime import datetime
    import random
    
    # Create a rollback deployment record
    rollback_deployment = {
        'timestamp': datetime.now().isoformat(),
        'commit': f"{random.randint(10000000, 99999999):08x}",
        'changes': 1,
        'success': True,
        'type': 'rollback',
        'rolled_back_deployment': deployment_name
    }
    
    # Add to deployment history
    gitops_status['deployments'].append(rollback_deployment)
    
    # Update metrics
    gitops_status['metrics']['total_deployments'] += 1
    gitops_status['metrics']['successful_deployments'] += 1
    gitops_status['running'] = True
    gitops_status['last_sync'] = datetime.now().isoformat()
    
    # Keep last 50 deployments
    if len(gitops_status['deployments']) > 50:
        gitops_status['deployments'] = gitops_status['deployments'][-50:]
    
    return {
        'status': 'rollback_initiated',
        'deployment': deployment_name,
        'rollback_deployment': rollback_deployment,
        'message': f'Rollback initiated for {deployment_name}'
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'gitops-dashboard'}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    try:
        while True:
            # Send status updates every 2 seconds
            await websocket.send_json(gitops_status)
            await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
