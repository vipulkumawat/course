"""
Day 57: Full-Text Search with Ranking System
Main application entry point
"""
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from search.engine import SearchEngine
from ranking.scoring import RankingEngine
from models.search_models import SearchQuery, SearchResponse
from utils.config import get_settings

settings = get_settings()

# Global instances
search_engine = None
ranking_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global search_engine, ranking_engine
    search_engine = SearchEngine()
    ranking_engine = RankingEngine()
    
    await search_engine.initialize()
    await ranking_engine.initialize()
    
    yield
    
    # Shutdown
    await search_engine.cleanup()
    await ranking_engine.cleanup()

app = FastAPI(
    title="Log Search with Ranking System",
    description="Day 57: Intelligent log search with relevance ranking",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Log Search with Ranking System - Day 57"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {
        "status": "healthy",
        "service": "log-search-ranking",
        "version": "1.0.0"
    }

@app.post("/api/search", response_model=SearchResponse)
async def search_logs(query: SearchQuery):
    """Search logs with intelligent ranking"""
    try:
        # Parse and expand query
        parsed_query = await search_engine.parse_query(query.query)
        
        # Execute search
        search_results = await search_engine.search(parsed_query)
        
        # Apply ranking
        ranked_results = await ranking_engine.rank_results(
            search_results, 
            query,
            context=query.context
        )
        
        return SearchResponse(
            query=query.query,
            results=ranked_results,
            total_hits=len(search_results),
            ranked_hits=len(ranked_results),
            execution_time_ms=search_results.get('execution_time', 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/suggestions")
async def get_search_suggestions(q: str):
    """Get search suggestions and auto-completion"""
    suggestions = await search_engine.get_suggestions(q)
    return {"suggestions": suggestions}

@app.get("/api/search/stats")
async def get_search_stats():
    """Get search system statistics"""
    stats = await search_engine.get_stats()
    ranking_stats = await ranking_engine.get_stats()
    
    return {
        "search_stats": stats,
        "ranking_stats": ranking_stats,
        "system_health": "healthy"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
