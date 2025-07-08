from fastapi import APIRouter
import redis
from elasticsearch import Elasticsearch

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "log-search-api"}

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with dependency status"""
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check Redis
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        health_status["services"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Check Elasticsearch
    try:
        es = Elasticsearch([{"host": "localhost", "port": 9200}])
        es.cluster.health()
        health_status["services"]["elasticsearch"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["elasticsearch"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    return health_status
