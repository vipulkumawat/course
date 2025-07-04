from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from ..models.log_entry import LogEntry
from ..services.log_generator import LogGenerator
from ..services.facet_engine import FacetEngine
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/logs", tags=["logs"])

# Global instances
log_generator = LogGenerator()
facet_engine = FacetEngine()

@router.post("/generate")
async def generate_sample_logs(count: int = 100, background_tasks: BackgroundTasks = None):
    """Generate and index sample logs"""
    try:
        logger.info(f"Generating {count} sample logs")
        logs = log_generator.generate_logs(count)
        
        # Index logs in background
        if background_tasks:
            background_tasks.add_task(index_logs_batch, logs)
        else:
            await index_logs_batch(logs)
            
        return {"message": f"Generated {count} logs", "status": "success"}
    except Exception as e:
        logger.error(f"Log generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index")
async def index_log(log_entry: LogEntry):
    """Index a single log entry"""
    try:
        await facet_engine.index_log(log_entry)
        return {"message": "Log indexed successfully", "log_id": log_entry.id}
    except Exception as e:
        logger.error(f"Log indexing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def index_logs_batch(logs: List[LogEntry]):
    """Index a batch of logs"""
    for log in logs:
        await facet_engine.index_log(log)
    logger.info(f"Indexed {len(logs)} logs")
