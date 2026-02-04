"""
FastAPI server exposing impact analysis endpoints
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from datetime import datetime

from impact_analyzer import ImpactAnalyzer, ChangeProposal, create_sample_dependency_graph
from risk_calculator import RiskCalculator

app = FastAPI(title="Change Impact Analysis API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzer
graph, metadata = create_sample_dependency_graph()
analyzer = ImpactAnalyzer(graph, metadata)
risk_calc = RiskCalculator()

class ChangeRequest(BaseModel):
    change_type: str
    target_service: str
    change_description: str
    proposed_by: Optional[str] = "api_user"

class AnalysisResponse(BaseModel):
    risk_score: float
    blast_radius: int
    affected_services: List[str]
    critical_path: bool
    recommendations: List[str]
    dependency_depth: dict
    timestamp: str

@app.get("/")
async def root():
    return {
        "service": "Change Impact Analysis API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services_monitored": len(graph.nodes),
        "dependencies_tracked": len(graph.edges),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_change(request: ChangeRequest):
    """Analyze impact of proposed change"""
    try:
        proposal = ChangeProposal(
            change_type=request.change_type,
            target_service=request.target_service,
            change_description=request.change_description,
            proposed_by=request.proposed_by
        )
        
        result = analyzer.analyze_change(proposal)
        
        # Apply historical risk adjustment
        adjusted_risk = risk_calc.get_adjusted_risk(
            result.risk_score, 
            proposal.change_type
        )
        
        return AnalysisResponse(
            risk_score=adjusted_risk,
            blast_radius=result.blast_radius,
            affected_services=result.affected_services,
            critical_path=result.critical_path,
            recommendations=result.recommendations,
            dependency_depth=result.dependency_depth,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/services")
async def list_services():
    """List all monitored services"""
    services_info = []
    for service in graph.nodes:
        meta = metadata.get(service, {})
        services_info.append({
            "name": service,
            "critical": meta.get('critical', False),
            "criticality": meta.get('criticality', 1),
            "sla": meta.get('sla', 'N/A'),
            "dependencies": list(graph.successors(service))
        })
    return {"services": services_info, "total": len(services_info)}

@app.get("/service/{service_name}/dependencies")
async def get_service_dependencies(service_name: str):
    """Get dependency tree for specific service"""
    if service_name not in graph:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Get all downstream dependencies
    affected, depth_map = analyzer._traverse_dependencies(service_name)
    
    return {
        "service": service_name,
        "total_dependencies": len(affected) - 1,  # Exclude self
        "dependency_tree": depth_map,
        "affected_services": sorted(affected)
    }

if __name__ == "__main__":
    print("🚀 Starting Change Impact Analysis API Server...")
    print("📊 Loaded services:", len(graph.nodes))
    print("🔗 Tracked dependencies:", len(graph.edges))
    print("\n🌐 Server running at http://localhost:8000")
    print("📖 API docs available at http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
