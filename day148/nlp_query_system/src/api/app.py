from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import redis

from config.config import Config
from src.nlp.nlp_service import NLPQueryService
from src.db.database import DatabaseManager

app = FastAPI(title="NLP Query System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
try:
    redis_client = redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=Config.REDIS_DB,
        decode_responses=True
    )
    redis_client.ping()
except:
    redis_client = None
    print("Redis not available, using local context storage")

db_manager = DatabaseManager(Config.get_db_url())
db_manager.connect()

schema_fields = db_manager.get_schema_fields()
nlp_service = NLPQueryService(schema_fields, redis_client)

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    success: bool
    message: str
    results: list
    suggestions: list
    metadata: dict
    sql_query: Optional[str] = None

@app.get("/")
async def root():
    """Serve the main UI"""
    return FileResponse("src/ui/index.html")

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process natural language query"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process query through NLP pipeline
        processed = nlp_service.process_query(request.query, session_id)
        
        # Execute generated SQL query
        results = db_manager.execute_query(processed['sql_query'])
        
        # Format results
        formatted = nlp_service.format_results(
            processed['intent'],
            results,
            processed['entities'],
            request.query
        )
        
        return QueryResponse(
            success=True,
            message=formatted['message'],
            results=formatted['results'][:10],  # Limit to 10 results
            suggestions=formatted.get('suggestions', []),
            metadata={
                'session_id': session_id,
                'intent': processed['intent'],
                'confidence': processed['confidence'],
                'total_results': len(results)
            },
            sql_query=processed['sql_query']
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "database": db_manager.conn is not None,
            "redis": redis_client is not None,
            "nlp": True
        }
    }

@app.get("/api/examples")
async def get_examples():
    """Get example queries"""
    return {
        "examples": [
            "Show me errors from payment service in the last hour",
            "How many warnings occurred today?",
            "Find logs from auth service yesterday",
            "What caused the errors in user service?",
            "Count errors in the last 30 minutes",
            "Show me all logs with level error",
            "Display info logs from api gateway"
        ]
    }
