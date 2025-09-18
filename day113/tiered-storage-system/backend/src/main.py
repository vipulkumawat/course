import asyncio
import json
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Thread

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog

from .tiers.manager import TierManager, get_tier_manager
from .policies.engine import TierType
from .query.router import QueryRouter
from .policies.engine import PolicyEngine

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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Configuration
config = {
    "HOT_STORAGE_PATH": "./data/hot",
    "WARM_STORAGE_PATH": "./data/warm", 
    "COLD_STORAGE_PATH": "./data/cold",
    "ARCHIVE_STORAGE_PATH": "./data/archive",
    "HOT_TO_WARM_DAYS": 2,  # Shorter for demo
    "WARM_TO_COLD_DAYS": 5,
    "COLD_TO_ARCHIVE_DAYS": 10,
    "MIGRATION_BATCH_SIZE": 100,
    "HOT_TIER_COST": 200.0,
    "WARM_TIER_COST": 50.0,
    "COLD_TIER_COST": 10.0,
    "ARCHIVE_TIER_COST": 1.0
}

# Initialize components
tier_manager = get_tier_manager(config)
query_router = QueryRouter(tier_manager)

# FastAPI app
app = FastAPI(title="Tiered Storage System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class LogEntryRequest(BaseModel):
    message: str
    level: str = "INFO"
    service: str = "default"
    priority: str = "normal"
    metadata: Dict = {}

class MigrationRequest(BaseModel):
    from_tier: str
    to_tier: str
    entry_ids: List[str]

# API Endpoints
@app.post("/api/logs")
async def store_log_entry(request: LogEntryRequest):
    """Store a new log entry"""
    try:
        log_data = {
            "message": request.message,
            "level": request.level,
            "service": request.service,
            "priority": request.priority,
            "metadata": request.metadata,
            "timestamp": datetime.now().isoformat()
        }
        
        entry_id = await tier_manager.store_log_entry(log_data)
        
        return {
            "status": "success",
            "entry_id": entry_id,
            "tier": "hot",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to store log entry", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/{entry_id}")
async def get_log_entry(entry_id: str):
    """Retrieve a specific log entry"""
    try:
        log_data = await query_router.query_log_entry(entry_id)
        
        if not log_data:
            raise HTTPException(status_code=404, detail="Log entry not found")
        
        return log_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve log entry", entry_id=entry_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
async def search_logs(q: str = "", tier: Optional[str] = None):
    """Search logs by content"""
    try:
        results = await query_router.search_logs(q, tier)
        
        return {
            "query": q,
            "tier_filter": tier,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error("Search failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/migrate")
async def manual_migration(request: MigrationRequest):
    """Manually trigger data migration"""
    try:
        from_tier = TierType(request.from_tier.lower())
        to_tier = TierType(request.to_tier.lower())
        
        result = await tier_manager.migrate_data(from_tier, to_tier, request.entry_ids)
        
        return {
            "status": "success",
            "migration_result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {str(e)}")
    except Exception as e:
        logger.error("Migration failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_statistics():
    """Get comprehensive system statistics"""
    try:
        tier_stats = await tier_manager.get_tier_statistics()
        query_stats = query_router.get_query_statistics()
        
        return {
            "tier_statistics": tier_stats,
            "query_statistics": query_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get statistics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-migrate")
async def trigger_auto_migration():
    """Trigger automatic migration process"""
    try:
        candidates = await tier_manager.evaluate_migration_candidates()
        migration_results = {}
        
        for (from_tier, to_tier), entry_ids in candidates.items():
            if entry_ids:
                result = await tier_manager.migrate_data(from_tier, to_tier, entry_ids)
                migration_results[f"{from_tier.value}_to_{to_tier.value}"] = result
        
        return {
            "status": "success",
            "migrations_performed": len(migration_results),
            "results": migration_results
        }
        
    except Exception as e:
        logger.error("Auto migration failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Background task for automatic migration
def run_auto_migration():
    """Run automatic migration process"""
    async def migrate():
        try:
            candidates = await tier_manager.evaluate_migration_candidates()
            
            for (from_tier, to_tier), entry_ids in candidates.items():
                if entry_ids:
                    logger.info("Starting automatic migration", 
                               from_tier=from_tier.value, 
                               to_tier=to_tier.value, 
                               count=len(entry_ids))
                    
                    result = await tier_manager.migrate_data(from_tier, to_tier, entry_ids)
                    logger.info("Migration completed", result=result)
        
        except Exception as e:
            logger.error("Automatic migration failed", error=str(e))
    
    asyncio.run(migrate())

# Schedule automatic migrations
schedule.every(10).minutes.do(run_auto_migration)

def run_scheduler():
    """Run the migration scheduler"""
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start scheduler in background thread
scheduler_thread = Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
