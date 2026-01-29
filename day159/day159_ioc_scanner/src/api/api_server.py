from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import redis
import asyncio
import structlog
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict, deque
from src.scanner.ioc_database import IOCDatabase
from src.scanner.models import IOCIndicator, IOCType, Severity
from src.matcher.matcher_engine import IOCMatcherEngine
from src.feeds.feed_manager import ThreatFeedManager
from config.config import config

logger = structlog.get_logger()

app = FastAPI(title="IOC Scanner API", version="1.0.0")

# Alert storage and lifecycle tracking
alert_store = []  # In-memory store (use Redis in production)
alert_lifecycle = {
    "new": 0,
    "acknowledged": 0,
    "investigating": 0,
    "resolved": 0,
    "false_positive": 0
}

# Performance SLA tracking
performance_metrics = {
    "scan_latencies": deque(maxlen=1000),
    "throughput_history": deque(maxlen=100),
    "avg_latency_ms": 0.0,
    "p95_latency_ms": 0.0,
    "p99_latency_ms": 0.0,
    "throughput_logs_per_sec": 0.0,
    "sla_target_ms": 50.0,
    "sla_compliance_rate": 100.0
}

# Severity scoring depth
severity_distribution = {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0,
    "info": 0
}

severity_score_ranges = {
    "critical": {"min": 90, "max": 100, "count": 0},
    "high": {"min": 70, "max": 89, "count": 0},
    "medium": {"min": 50, "max": 69, "count": 0},
    "low": {"min": 30, "max": 49, "count": 0},
    "info": {"min": 0, "max": 29, "count": 0}
}

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
redis_client = redis.Redis(
    host=config.redis_host,
    port=config.redis_port,
    db=config.redis_db,
    decode_responses=True
)

ioc_db = IOCDatabase(redis_client, config.cache_ttl)
matcher = IOCMatcherEngine(ioc_db, config.max_workers)
feed_manager = ThreatFeedManager(config.threat_feeds)

class LogScanRequest(BaseModel):
    logs: List[Dict[str, Any]]

class IOCAddRequest(BaseModel):
    value: str
    ioc_type: str
    severity: str
    source: str
    description: str = ""

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("IOC Scanner API starting up")
    
    # Load initial threat feeds
    try:
        iocs = await feed_manager.update_feeds()
        for ioc in iocs[:1000]:  # Limit initial load
            ioc_db.add_ioc(ioc)
        logger.info("Initial threat feeds loaded", count=len(iocs))
    except Exception as e:
        logger.error("Failed to load initial feeds", error=str(e))

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "healthy",
        "service": "IOC Scanner",
        "version": "1.0.0"
    }

def calculate_performance_metrics():
    """Calculate performance SLA metrics"""
    if performance_metrics["scan_latencies"]:
        latencies = sorted(performance_metrics["scan_latencies"])
        n = len(latencies)
        performance_metrics["avg_latency_ms"] = sum(latencies) / n
        performance_metrics["p95_latency_ms"] = latencies[int(n * 0.95)] if n > 0 else 0
        performance_metrics["p99_latency_ms"] = latencies[int(n * 0.99)] if n > 0 else 0
        
        # Calculate SLA compliance
        sla_compliant = sum(1 for l in latencies if l <= performance_metrics["sla_target_ms"])
        performance_metrics["sla_compliance_rate"] = (sla_compliant / n * 100) if n > 0 else 100.0
    
    if performance_metrics["throughput_history"]:
        performance_metrics["throughput_logs_per_sec"] = sum(performance_metrics["throughput_history"]) / len(performance_metrics["throughput_history"])

def get_ioc_coverage_breadth():
    """Calculate IOC coverage breadth metrics"""
    coverage = {
        "by_type": {},
        "by_severity": dict(severity_distribution),
        "total_unique_iocs": ioc_db.stats["total_iocs"],
        "coverage_percentage": {}
    }
    
    # Get IOC type distribution from Redis
    for ioc_type in IOCType:
        try:
            count = redis_client.scard(f"ioc_index:{ioc_type.value}")
            coverage["by_type"][ioc_type.value] = count
        except:
            coverage["by_type"][ioc_type.value] = 0
    
    # Calculate coverage percentage
    total = sum(coverage["by_type"].values())
    for ioc_type, count in coverage["by_type"].items():
        coverage["coverage_percentage"][ioc_type] = (count / total * 100) if total > 0 else 0
    
    return coverage

def get_feed_quality_metrics():
    """Calculate feed quality metrics"""
    feed_stats = feed_manager.get_stats()
    
    # Calculate freshness (time since last update)
    freshness_hours = 0
    if feed_stats.get("last_update"):
        try:
            last_update = datetime.fromisoformat(feed_stats["last_update"])
            freshness_hours = (datetime.now() - last_update).total_seconds() / 3600
        except:
            pass
    
    # Calculate completeness (IOCs extracted vs expected)
    expected_iocs = feed_stats.get("feeds_processed", 0) * 50000  # Rough estimate
    completeness = (feed_stats.get("iocs_extracted", 0) / expected_iocs * 100) if expected_iocs > 0 else 0
    completeness = min(completeness, 100)
    
    # Accuracy (based on error rate)
    total_operations = feed_stats.get("feeds_processed", 0) + feed_stats.get("errors", 0)
    accuracy = ((total_operations - feed_stats.get("errors", 0)) / total_operations * 100) if total_operations > 0 else 100
    
    return {
        "freshness_hours": round(freshness_hours, 2),
        "freshness_status": "fresh" if freshness_hours < 24 else "stale" if freshness_hours < 72 else "outdated",
        "completeness_percentage": round(completeness, 2),
        "accuracy_percentage": round(accuracy, 2),
        "feeds_processed": feed_stats.get("feeds_processed", 0),
        "iocs_extracted": feed_stats.get("iocs_extracted", 0),
        "error_rate": round((feed_stats.get("errors", 0) / total_operations * 100) if total_operations > 0 else 0, 2)
    }

@app.get("/stats")
async def get_stats():
    """Get comprehensive system statistics"""
    calculate_performance_metrics()
    
    return {
        "ioc_database": ioc_db.get_stats(),
        "matcher": matcher.get_stats(),
        "feed_manager": feed_manager.get_stats(),
        "severity_scoring": {
            "distribution": dict(severity_distribution),
            "score_ranges": dict(severity_score_ranges),
            "avg_confidence": sum(severity_score_ranges[s]["count"] * (severity_score_ranges[s]["min"] + severity_score_ranges[s]["max"]) / 2 
                                  for s in severity_score_ranges) / max(sum(severity_score_ranges[s]["count"] for s in severity_score_ranges), 1)
        },
        "ioc_coverage": get_ioc_coverage_breadth(),
        "performance_slas": dict(performance_metrics),
        "feed_quality": get_feed_quality_metrics(),
        "alert_lifecycle": {
            "current_state": dict(alert_lifecycle),
            "total_alerts": len(alert_store),
            "recent_alerts_24h": len([a for a in alert_store if (datetime.now() - datetime.fromisoformat(a["timestamp"])).total_seconds() < 86400])
        }
    }

@app.post("/scan")
async def scan_logs(request: LogScanRequest):
    """Scan logs for IOC matches"""
    try:
        start_time = time.time()
        alerts = matcher.scan_batch(request.logs)
        scan_duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Track performance
        performance_metrics["scan_latencies"].append(scan_duration)
        if len(request.logs) > 0:
            throughput = len(request.logs) / (scan_duration / 1000)
            performance_metrics["throughput_history"].append(throughput)
        
        # Store alerts and track lifecycle
        alert_dicts = []
        for alert in alerts:
            alert_dict = alert.to_dict()
            alert_dict["lifecycle_state"] = "new"
            alert_store.append(alert_dict)
            alert_lifecycle["new"] += 1
            
            # Track severity distribution
            severity = alert.severity.value.lower()
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
            
            # Track severity score ranges
            score = alert.confidence_score
            for range_name, range_data in severity_score_ranges.items():
                if range_data["min"] <= score <= range_data["max"]:
                    range_data["count"] += 1
                    break
            
            alert_dicts.append(alert_dict)
        
        # Keep only last 1000 alerts
        if len(alert_store) > 1000:
            alert_store[:] = alert_store[-1000:]
        
        return {
            "scanned": len(request.logs),
            "alerts": alert_dicts,
            "alert_count": len(alerts),
            "scan_duration_ms": round(scan_duration, 2)
        }
    except Exception as e:
        logger.error("Scan error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ioc/add")
async def add_ioc(request: IOCAddRequest):
    """Manually add IOC"""
    try:
        ioc = IOCIndicator(
            value=request.value,
            ioc_type=IOCType(request.ioc_type),
            severity=Severity(request.severity),
            source=request.source,
            description=request.description
        )
        
        success = ioc_db.add_ioc(ioc)
        
        if success:
            return {"status": "success", "ioc": ioc.to_dict()}
        else:
            raise HTTPException(status_code=500, detail="Failed to add IOC")
    
    except Exception as e:
        logger.error("Add IOC error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/feeds/update")
async def update_feeds(background_tasks: BackgroundTasks):
    """Trigger threat feed update"""
    async def update_task():
        iocs = await feed_manager.update_feeds()
        for ioc in iocs:
            ioc_db.add_ioc(ioc)
    
    background_tasks.add_task(update_task)
    return {"status": "update_started"}

@app.get("/alerts/recent")
async def get_recent_alerts(limit: int = 50):
    """Get recent alerts with lifecycle information"""
    recent = sorted(alert_store, key=lambda x: x["timestamp"], reverse=True)[:limit]
    return {
        "alerts": recent,
        "count": len(recent),
        "lifecycle_summary": dict(alert_lifecycle)
    }

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    for alert in alert_store:
        if alert["alert_id"] == alert_id:
            if alert["lifecycle_state"] == "new":
                alert["lifecycle_state"] = "acknowledged"
                alert["acknowledged"] = True
                alert_lifecycle["new"] = max(0, alert_lifecycle["new"] - 1)
                alert_lifecycle["acknowledged"] += 1
                return {"status": "acknowledged", "alert_id": alert_id}
    raise HTTPException(status_code=404, detail="Alert not found")

@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, false_positive: bool = False):
    """Resolve an alert"""
    for alert in alert_store:
        if alert["alert_id"] == alert_id:
            old_state = alert["lifecycle_state"]
            if false_positive:
                alert["lifecycle_state"] = "false_positive"
                alert_lifecycle["false_positive"] += 1
            else:
                alert["lifecycle_state"] = "resolved"
                alert_lifecycle["resolved"] += 1
            
            # Decrement old state
            if old_state in alert_lifecycle:
                alert_lifecycle[old_state] = max(0, alert_lifecycle[old_state] - 1)
            
            return {"status": "resolved", "alert_id": alert_id, "false_positive": false_positive}
    raise HTTPException(status_code=404, detail="Alert not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.api_host, port=config.api_port)
