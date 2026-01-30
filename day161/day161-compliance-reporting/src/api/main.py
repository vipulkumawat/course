from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compliance.rule_engine import ComplianceRuleEngine, ComplianceFramework
from evidence.collector import EvidenceCollector
from reports.generator import ComplianceReportGenerator

app = FastAPI(title="Security Compliance Reporting API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
rule_engine = ComplianceRuleEngine()
evidence_collector = EvidenceCollector()
report_generator = ComplianceReportGenerator()

# Sync rule engine evidence counts with loaded evidence
def sync_rule_engine_evidence():
    """Sync rule engine evidence counts with loaded evidence"""
    for entry in evidence_collector.evidence_store:
        for match in entry.compliance_matches:
            framework_str = match["framework"]
            req_id = match["requirement_id"]
            
            # Convert string to enum
            try:
                framework_enum = ComplianceFramework[framework_str.upper()]
                if req_id in rule_engine.evidence_counts[framework_enum]:
                    rule_engine.evidence_counts[framework_enum][req_id] += 1
            except KeyError:
                continue

# Sync on startup
sync_rule_engine_evidence()

class LogEvent(BaseModel):
    event_type: str
    timestamp: str
    details: Dict[str, Any]

class ComplianceStats(BaseModel):
    framework: str
    coverage_percentage: float
    total_requirements: int
    requirements_with_evidence: int
    gaps: List[str]

@app.get("/")
async def root():
    return {
        "service": "Security Compliance Reporting API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.post("/api/events/ingest")
async def ingest_log_event(log_event: LogEvent):
    """Ingest and process security log event"""
    event_data = {
        "event_type": log_event.event_type,
        "timestamp": log_event.timestamp,
        **log_event.details
    }
    
    # Evaluate against compliance rules
    matches = rule_engine.evaluate_log_event(event_data)
    
    # Collect evidence if matches found
    evidence_id = None
    if matches:
        evidence_id = evidence_collector.collect(event_data, matches)
    
    return {
        "status": "processed",
        "evidence_id": evidence_id,
        "compliance_matches": len(matches),
        "frameworks_affected": list(set(m["framework"] for m in matches))
    }

@app.get("/api/compliance/coverage/{framework}")
async def get_compliance_coverage(framework: str):
    """Get compliance coverage for specific framework"""
    try:
        framework_enum = ComplianceFramework[framework.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid framework: {framework}")
    
    coverage = rule_engine.get_compliance_coverage(framework_enum)
    gaps = rule_engine.identify_gaps(framework_enum)
    
    return {
        **coverage,
        "gaps": gaps,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/compliance/coverage")
async def get_all_coverage():
    """Get compliance coverage for all frameworks"""
    all_coverage = {}
    for framework in ComplianceFramework:
        coverage = rule_engine.get_compliance_coverage(framework)
        gaps = rule_engine.identify_gaps(framework)
        all_coverage[framework.value] = {
            **coverage,
            "gaps": gaps
        }
    
    return all_coverage

@app.get("/api/evidence/{framework}/{requirement_id}")
async def get_evidence(framework: str, requirement_id: str, limit: int = 10):
    """Get evidence for specific requirement"""
    evidence = evidence_collector.get_evidence_by_requirement(
        framework, requirement_id, limit
    )
    
    return {
        "framework": framework,
        "requirement_id": requirement_id,
        "evidence_count": evidence_collector.get_evidence_count(framework, requirement_id),
        "evidence": evidence
    }

@app.post("/api/reports/generate/{framework}")
async def generate_report(framework: str, background_tasks: BackgroundTasks):
    """Generate compliance report for framework"""
    try:
        framework_enum = ComplianceFramework[framework.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid framework: {framework}")
    
    coverage = rule_engine.get_compliance_coverage(framework_enum)
    gaps = rule_engine.identify_gaps(framework_enum)
    evidence_data = {}
    
    # Generate appropriate report
    if framework_enum == ComplianceFramework.PCI_DSS:
        report_path = report_generator.generate_pci_dss_report(coverage, evidence_data, gaps)
    elif framework_enum == ComplianceFramework.SOC2:
        report_path = report_generator.generate_soc2_report(coverage, evidence_data, gaps)
    elif framework_enum == ComplianceFramework.ISO27001:
        report_path = report_generator.generate_iso27001_report(coverage, evidence_data, gaps)
    elif framework_enum == ComplianceFramework.HIPAA:
        report_path = report_generator.generate_hipaa_report(coverage, evidence_data, gaps)
    else:
        raise HTTPException(status_code=501, detail=f"Report generation not implemented for {framework}")
    
    return {
        "status": "generated",
        "framework": framework,
        "report_path": report_path,
        "coverage": coverage['coverage_percentage'],
        "gaps": len(gaps)
    }

@app.post("/api/reports/generate/multi-framework")
async def generate_multi_framework_report():
    """Generate combined report for all frameworks"""
    all_coverage = {}
    all_gaps = {}
    
    for framework in ComplianceFramework:
        coverage = rule_engine.get_compliance_coverage(framework)
        gaps = rule_engine.identify_gaps(framework)
        all_coverage[framework.value] = coverage
        all_gaps[framework.value] = gaps
    
    report_path = report_generator.generate_multi_framework_report(all_coverage, all_gaps)
    
    return {
        "status": "generated",
        "report_path": report_path,
        "frameworks": list(all_coverage.keys())
    }

@app.get("/api/evidence/verify")
async def verify_evidence_integrity():
    """Verify integrity of all stored evidence"""
    return evidence_collector.verify_all_integrity()

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    stats = {}
    
    for framework in ComplianceFramework:
        coverage = rule_engine.get_compliance_coverage(framework)
        gaps = rule_engine.identify_gaps(framework)
        
        stats[framework.value] = {
            "coverage_percentage": coverage['coverage_percentage'],
            "requirements_with_evidence": coverage['requirements_with_evidence'],
            "total_requirements": coverage['total_requirements'],
            "gap_count": len(gaps),
            "status": "compliant" if coverage['coverage_percentage'] >= 80 else "non-compliant"
        }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "frameworks": stats,
        "total_evidence": len(evidence_collector.evidence_store)
    }

@app.get("/api/reports/download/{filename}")
async def download_report(filename: str):
    """Download a generated report PDF"""
    report_path = os.path.join("data/reports", filename)
    
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail=f"Report not found: {filename}")
    
    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

@app.get("/api/reports/list")
async def list_reports():
    """List all available reports"""
    reports_dir = "data/reports"
    if not os.path.exists(reports_dir):
        return {"reports": []}
    
    reports = []
    for filename in os.listdir(reports_dir):
        if filename.endswith('.pdf'):
            filepath = os.path.join(reports_dir, filename)
            file_stat = os.stat(filepath)
            reports.append({
                "filename": filename,
                "size": file_stat.st_size,
                "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                "download_url": f"/api/reports/download/{filename}",
                "preview_url": f"/api/reports/download/{filename}"
            })
    
    # Sort by creation time, newest first
    reports.sort(key=lambda x: x["created"], reverse=True)
    
    return {"reports": reports}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
