from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class SLAAPI:
    def __init__(self, metrics, evaluator, alerts):
        self.app = FastAPI(title="SLA Monitor")
        self.metrics = metrics
        self.evaluator = evaluator
        self.alerts = alerts
        
        self.app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
        
        # Get project root directory (3 levels up from src/api/sla_api.py)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        web_dir = os.path.join(project_root, "web")
        
        # Mount static files if web directory exists
        if os.path.exists(web_dir):
            self.app.mount("/static", StaticFiles(directory=web_dir), name="static")
        
        self._setup()
    
    def _setup(self):
        @self.app.get("/")
        async def root():
            # Serve dashboard by default
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            dashboard_path = os.path.join(project_root, "web", "index.html")
            if os.path.exists(dashboard_path):
                return FileResponse(dashboard_path)
            return {"status": "online", "dashboard": "/dashboard"}
        
        @self.app.get("/dashboard")
        async def dashboard():
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            dashboard_path = os.path.join(project_root, "web", "index.html")
            if os.path.exists(dashboard_path):
                return FileResponse(dashboard_path)
            return {"error": "Dashboard not found"}
        
        @self.app.get("/api/slo/status")
        async def status():
            return JSONResponse(await self.evaluator.get_slo_status())
        
        @self.app.get("/api/violations")
        async def violations():
            v = await self.evaluator.get_violations()
            return JSONResponse([{
                "slo": x.slo_name,
                "tier": x.service_tier.value,
                "severity": x.severity,
                "actual": x.actual_value,
                "target": x.target_value,
                "duration": x.breach_duration_seconds
            } for x in v])
