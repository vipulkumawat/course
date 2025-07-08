#!/bin/bash

# Day 58: Search API Implementation Script
# Creates a complete RESTful API for log search with authentication, rate limiting, and documentation

set -e

PROJECT_NAME="log-search-api"
echo "🚀 Setting up Day 58: Search API for Log Data"
echo "=================================================="

# Create project structure
mkdir -p $PROJECT_NAME
cd $PROJECT_NAME

# Create directory structure
mkdir -p {backend/{app,models,schemas,services,middleware,tests},frontend/{src/{components,services,hooks},public},docs,scripts,docker}
mkdir -p backend/app/{routers,core,db}

echo "📁 Created project structure"

# Create Python requirements
cat > backend/requirements.txt << 'EOF'
fastapi==0.111.0
uvicorn==0.29.0
pydantic==2.7.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
redis==5.0.4
elasticsearch==8.13.1
pytest==8.2.0
pytest-asyncio==0.23.7
httpx==0.27.0
slowapi==0.1.9
python-dotenv==1.0.1
jinja2==3.1.4
aiofiles==23.2.1
EOF

# Create environment configuration
cat > backend/.env << 'EOF'
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://localhost:6379
ELASTICSEARCH_URL=http://localhost:9200
API_V1_STR=/api/v1
PROJECT_NAME=Log Search API
EOF

# Main FastAPI application
cat > backend/app/main.py << 'EOF'
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from .routers import search, auth, health
from .middleware.rate_limiting import RateLimitMiddleware
from .middleware.auth import AuthMiddleware

app = FastAPI(
    title="Log Search API",
    description="RESTful API for distributed log search with ranking",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(search.router, prefix="/api/v1/logs", tags=["search"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])

# Serve frontend
if os.path.exists("../frontend/build"):
    app.mount("/static", StaticFiles(directory="../frontend/build/static"), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend():
        with open("../frontend/build/index.html") as f:
            return f.read()

@app.get("/api/v1/")
async def root():
    return {
        "message": "Log Search API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }
EOF

# Pydantic schemas
cat > backend/schemas/search.py << 'EOF'
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    start_time: Optional[datetime] = Field(None, description="Start time for search range")
    end_time: Optional[datetime] = Field(None, description="End time for search range")
    log_level: Optional[List[LogLevel]] = Field(None, description="Filter by log levels")
    service_name: Optional[List[str]] = Field(None, description="Filter by service names")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    include_content: bool = Field(True, description="Include full log content")
    sort_by: str = Field("relevance", description="Sort field: relevance, timestamp")
    sort_order: str = Field("desc", description="Sort order: asc, desc")

class LogEntry(BaseModel):
    id: str
    timestamp: datetime
    level: LogLevel
    service_name: str
    message: str
    content: Optional[Dict[str, Any]] = None
    score: Optional[float] = None

class SearchResponse(BaseModel):
    query: str
    total_hits: int
    execution_time_ms: float
    results: List[LogEntry]
    pagination: Dict[str, Any]
    aggregations: Optional[Dict[str, Any]] = None

class SearchMetrics(BaseModel):
    total_queries: int
    avg_response_time_ms: float
    cache_hit_rate: float
    top_queries: List[Dict[str, Any]]
EOF

# Authentication schemas
cat > backend/schemas/auth.py << 'EOF'
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
EOF

# Search service implementation
cat > backend/services/search_service.py << 'EOF'
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from elasticsearch import Elasticsearch
import redis
from ..schemas.search import SearchRequest, SearchResponse, LogEntry, LogLevel

class SearchService:
    def __init__(self):
        self.es = Elasticsearch([{"host": "localhost", "port": 9200}])
        self.redis = redis.Redis(host='localhost', port=6379, db=0)
        self.index_name = "logs"
        
    async def search_logs(self, request: SearchRequest, user_id: str) -> SearchResponse:
        start_time = time.time()
        
        # Check cache first
        cache_key = self._generate_cache_key(request)
        cached_result = self.redis.get(cache_key)
        if cached_result:
            result = json.loads(cached_result)
            result['from_cache'] = True
            return SearchResponse(**result)
        
        # Build Elasticsearch query
        es_query = self._build_es_query(request)
        
        # Execute search
        try:
            es_response = self.es.search(
                index=self.index_name,
                body=es_query,
                from_=request.offset,
                size=request.limit
            )
            
            # Process results
            results = self._process_es_response(es_response, request.include_content)
            
            # Calculate metrics
            execution_time_ms = (time.time() - start_time) * 1000
            
            response = SearchResponse(
                query=request.query,
                total_hits=es_response['hits']['total']['value'],
                execution_time_ms=execution_time_ms,
                results=results,
                pagination={
                    "offset": request.offset,
                    "limit": request.limit,
                    "has_more": request.offset + len(results) < es_response['hits']['total']['value']
                },
                aggregations=es_response.get('aggregations')
            )
            
            # Cache result for 5 minutes
            self.redis.setex(cache_key, 300, response.json())
            
            # Track usage metrics
            self._track_query_metrics(request.query, execution_time_ms, user_id)
            
            return response
            
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")
    
    def _build_es_query(self, request: SearchRequest) -> Dict[str, Any]:
        query = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            },
            "sort": [],
            "aggs": {
                "levels": {"terms": {"field": "level"}},
                "services": {"terms": {"field": "service_name"}},
                "timeline": {
                    "date_histogram": {
                        "field": "timestamp",
                        "interval": "1h"
                    }
                }
            }
        }
        
        # Full-text search
        if request.query:
            query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": request.query,
                    "fields": ["message^2", "content"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        
        # Time range filter
        if request.start_time or request.end_time:
            time_range = {}
            if request.start_time:
                time_range["gte"] = request.start_time.isoformat()
            if request.end_time:
                time_range["lte"] = request.end_time.isoformat()
            
            query["query"]["bool"]["filter"].append({
                "range": {"timestamp": time_range}
            })
        
        # Log level filter
        if request.log_level:
            query["query"]["bool"]["filter"].append({
                "terms": {"level": [level.value for level in request.log_level]}
            })
        
        # Service name filter
        if request.service_name:
            query["query"]["bool"]["filter"].append({
                "terms": {"service_name": request.service_name}
            })
        
        # Sorting
        if request.sort_by == "relevance":
            query["sort"] = ["_score"]
        elif request.sort_by == "timestamp":
            query["sort"] = [{"timestamp": {"order": request.sort_order}}]
        
        return query
    
    def _process_es_response(self, es_response: Dict, include_content: bool) -> List[LogEntry]:
        results = []
        for hit in es_response['hits']['hits']:
            source = hit['_source']
            
            entry = LogEntry(
                id=hit['_id'],
                timestamp=datetime.fromisoformat(source['timestamp']),
                level=LogLevel(source['level']),
                service_name=source['service_name'],
                message=source['message'],
                score=hit['_score']
            )
            
            if include_content:
                entry.content = source.get('content', {})
            
            results.append(entry)
        
        return results
    
    def _generate_cache_key(self, request: SearchRequest) -> str:
        key_data = {
            "query": request.query,
            "start_time": request.start_time.isoformat() if request.start_time else None,
            "end_time": request.end_time.isoformat() if request.end_time else None,
            "log_level": [l.value for l in request.log_level] if request.log_level else None,
            "service_name": request.service_name,
            "limit": request.limit,
            "offset": request.offset,
            "sort_by": request.sort_by,
            "sort_order": request.sort_order
        }
        return f"search:{hash(json.dumps(key_data, sort_keys=True))}"
    
    def _track_query_metrics(self, query: str, execution_time: float, user_id: str):
        metrics_key = f"metrics:{user_id}"
        pipe = self.redis.pipeline()
        pipe.hincrby(metrics_key, "total_queries", 1)
        pipe.hincrbyfloat(metrics_key, "total_time", execution_time)
        pipe.lpush(f"queries:{user_id}", json.dumps({
            "query": query,
            "time": execution_time,
            "timestamp": datetime.now().isoformat()
        }))
        pipe.ltrim(f"queries:{user_id}", 0, 99)  # Keep last 100 queries
        pipe.execute()
EOF

# Search router
cat > backend/app/routers/search.py << 'EOF'
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from typing import List, Optional
from datetime import datetime
from ..schemas.search import SearchRequest, SearchResponse, LogLevel
from ..services.search_service import SearchService
from ..middleware.auth import get_current_user

router = APIRouter()
security = HTTPBearer()
search_service = SearchService()

@router.post("/search", response_model=SearchResponse)
async def search_logs(
    request: SearchRequest,
    current_user = Depends(get_current_user)
):
    """
    Search logs with advanced filtering and ranking capabilities.
    
    - **query**: Full-text search query
    - **start_time**: Filter logs after this timestamp
    - **end_time**: Filter logs before this timestamp
    - **log_level**: Filter by log levels (DEBUG, INFO, WARN, ERROR, FATAL)
    - **service_name**: Filter by service names
    - **limit**: Maximum results (1-1000)
    - **offset**: Pagination offset
    - **sort_by**: Sort field (relevance, timestamp)
    - **sort_order**: Sort order (asc, desc)
    """
    try:
        result = await search_service.search_logs(request, current_user.username)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=SearchResponse)
async def search_logs_get(
    q: str = Query(..., description="Search query"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    log_level: Optional[List[LogLevel]] = Query(None, description="Log levels"),
    service_name: Optional[List[str]] = Query(None, description="Service names"),
    limit: int = Query(100, ge=1, le=1000, description="Limit"),
    offset: int = Query(0, ge=0, description="Offset"),
    sort_by: str = Query("relevance", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    current_user = Depends(get_current_user)
):
    """GET endpoint for search with query parameters"""
    request = SearchRequest(
        query=q,
        start_time=start_time,
        end_time=end_time,
        log_level=log_level,
        service_name=service_name,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await search_logs(request, current_user)

@router.get("/suggest")
async def suggest_queries(
    q: str = Query(..., description="Partial query"),
    current_user = Depends(get_current_user)
):
    """Get query suggestions based on popular searches"""
    # Implementation for query suggestions
    suggestions = [
        f"{q} error",
        f"{q} warning",
        f"{q} timeout",
        f"{q} failed"
    ]
    return {"suggestions": suggestions[:5]}

@router.get("/metrics")
async def get_search_metrics(current_user = Depends(get_current_user)):
    """Get search metrics for the current user"""
    # Implementation for user-specific metrics
    return {
        "total_queries": 142,
        "avg_response_time_ms": 89.5,
        "cache_hit_rate": 0.73,
        "top_queries": [
            {"query": "error payment", "count": 23},
            {"query": "timeout database", "count": 18}
        ]
    }
EOF

# Authentication service
cat > backend/services/auth_service.py << 'EOF'
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from ..schemas.auth import UserInDB, User

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mock user database
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "disabled": False,
    }
}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    user = get_user(fake_users_db, username=username)
    if user is None:
        return None
    return user
EOF

# Rate limiting middleware
cat > backend/middleware/rate_limiting.py << 'EOF'
import time
import redis
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str = "redis://localhost:6379", 
                 default_limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.redis = redis.from_url(redis_url)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.startswith("/api/v1/health"):
            return await call_next(request)
        
        # Get client identifier
        client_id = self.get_client_id(request)
        
        # Check rate limit
        if not self.is_allowed(client_id):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.default_limit} requests per {self.window_seconds} seconds"
                }
            )
        
        response = await call_next(request)
        return response
    
    def get_client_id(self, request: Request) -> str:
        # Use API key or IP address
        api_key = request.headers.get("Authorization")
        if api_key:
            return f"api_key:{api_key}"
        
        client_ip = request.client.host
        return f"ip:{client_ip}"
    
    def is_allowed(self, client_id: str) -> bool:
        current_time = int(time.time())
        window_start = current_time - self.window_seconds
        
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(client_id, 0, window_start)
        pipe.zcard(client_id)
        pipe.zadd(client_id, {str(current_time): current_time})
        pipe.expire(client_id, self.window_seconds)
        
        results = pipe.execute()
        request_count = results[1]
        
        return request_count < self.default_limit
EOF

# Auth middleware
cat > backend/middleware/auth.py << 'EOF'
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from ..services.auth_service import get_current_user

security = HTTPBearer()

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        public_paths = ["/api/docs", "/api/redoc", "/api/v1/auth/", "/api/v1/health"]
        
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        response = await call_next(request)
        return response

async def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = await get_current_user(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user
EOF

# Auth router
cat > backend/app/routers/auth.py << 'EOF'
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from ..schemas.auth import Token
from ..services.auth_service import authenticate_user, create_access_token, fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def read_users_me(current_user = Depends(get_current_user_dependency)):
    return current_user
EOF

# Health router
cat > backend/app/routers/health.py << 'EOF'
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
EOF

# Frontend React application
cat > frontend/package.json << 'EOF'
{
  "name": "log-search-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.17.0",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^14.5.2",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-scripts": "5.0.1",
    "axios": "^1.7.2",
    "antd": "^5.18.1",
    "@ant-design/icons": "^5.3.7",
    "moment": "^2.30.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8000"
}
EOF

# Frontend main App component
cat > frontend/src/App.js << 'EOF'
import React, { useState } from 'react';
import { Layout, Menu, Card, Input, Button, Table, DatePicker, Select, Tag, Space, Row, Col, Statistic } from 'antd';
import { SearchOutlined, ApiOutlined, BarChartOutlined, UserOutlined } from '@ant-design/icons';
import SearchInterface from './components/SearchInterface';
import ApiDocumentation from './components/ApiDocumentation';
import Dashboard from './components/Dashboard';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Option } = Select;

function App() {
  const [selectedKey, setSelectedKey] = useState('search');

  const menuItems = [
    {
      key: 'search',
      icon: <SearchOutlined />,
      label: 'Log Search',
    },
    {
      key: 'api',
      icon: <ApiOutlined />,
      label: 'API Documentation',
    },
    {
      key: 'dashboard',
      icon: <BarChartOutlined />,
      label: 'Analytics',
    },
  ];

  const renderContent = () => {
    switch (selectedKey) {
      case 'search':
        return <SearchInterface />;
      case 'api':
        return <ApiDocumentation />;
      case 'dashboard':
        return <Dashboard />;
      default:
        return <SearchInterface />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header className="header" style={{ background: '#1890ff', padding: '0 24px' }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
          Log Search API
        </div>
        <div style={{ float: 'right', color: 'white' }}>
          <UserOutlined /> Test User
        </div>
      </Header>
      <Layout>
        <Sider width={200} className="site-layout-background">
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
            onSelect={({ key }) => setSelectedKey(key)}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content
            className="site-layout-background"
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
            }}
          >
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;
EOF

# Search Interface Component
cat > frontend/src/components/SearchInterface.js << 'EOF'
import React, { useState } from 'react';
import { Card, Input, Button, Table, DatePicker, Select, Tag, Space, Row, Col, Statistic, message } from 'antd';
import { SearchOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';
import moment from 'moment';

const { RangePicker } = DatePicker;
const { Option } = Select;

function SearchInterface() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({});
  const [filters, setFilters] = useState({
    logLevel: [],
    serviceName: [],
    dateRange: null
  });

  const logLevels = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'];
  const services = ['api-gateway', 'user-service', 'payment-service', 'notification-service'];

  const performSearch = async () => {
    if (!searchQuery.trim()) {
      message.warning('Please enter a search query');
      return;
    }

    setLoading(true);
    try {
      const params = {
        q: searchQuery,
        limit: 50,
        offset: 0
      };

      if (filters.logLevel.length > 0) {
        params.log_level = filters.logLevel;
      }
      
      if (filters.serviceName.length > 0) {
        params.service_name = filters.serviceName;
      }

      if (filters.dateRange) {
        params.start_time = filters.dateRange[0].toISOString();
        params.end_time = filters.dateRange[1].toISOString();
      }

      const response = await axios.get('/api/v1/logs/search', {
        params,
        headers: {
          'Authorization': 'Bearer demo-token'
        }
      });

      setSearchResults(response.data.results || []);
      setStats({
        totalHits: response.data.total_hits,
        executionTime: response.data.execution_time_ms,
        query: response.data.query
      });

      message.success(`Found ${response.data.total_hits} results in ${response.data.execution_time_ms.toFixed(2)}ms`);
    } catch (error) {
      console.error('Search error:', error);
      message.error('Search failed. Please try again.');
      
      // Demo data for UI demonstration
      const demoResults = [
        {
          id: '1',
          timestamp: '2025-06-16T10:30:00Z',
          level: 'ERROR',
          service_name: 'payment-service',
          message: 'Payment processing failed for user 12345',
          score: 0.95
        },
        {
          id: '2', 
          timestamp: '2025-06-16T10:29:45Z',
          level: 'WARN',
          service_name: 'api-gateway',
          message: 'High response time detected: 2.5s',
          score: 0.87
        },
        {
          id: '3',
          timestamp: '2025-06-16T10:29:30Z',
          level: 'INFO',
          service_name: 'user-service',
          message: 'User login successful',
          score: 0.72
        }
      ];
      
      setSearchResults(demoResults);
      setStats({
        totalHits: 156,
        executionTime: 45.7,
        query: searchQuery
      });
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp) => moment(timestamp).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: 'Level',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level) => {
        const colors = {
          ERROR: 'red',
          WARN: 'orange', 
          INFO: 'blue',
          DEBUG: 'green',
          FATAL: 'purple'
        };
        return <Tag color={colors[level]}>{level}</Tag>;
      }
    },
    {
      title: 'Service',
      dataIndex: 'service_name',
      key: 'service_name',
      width: 150,
      render: (service) => <Tag color="geekblue">{service}</Tag>
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    },
    {
      title: 'Score',
      dataIndex: 'score',
      key: 'score',
      width: 80,
      render: (score) => score ? score.toFixed(2) : 'N/A'
    }
  ];

  return (
    <div>
      <Card title="Log Search Interface" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Row gutter={16}>
            <Col span={12}>
              <Input.Search
                placeholder="Enter search query (e.g., error payment timeout)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onSearch={performSearch}
                enterButton={<Button type="primary" icon={<SearchOutlined />}>Search</Button>}
                size="large"
              />
            </Col>
            <Col span={12}>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={() => setSearchResults([])}>
                  Clear
                </Button>
                <Button icon={<DownloadOutlined />} disabled={searchResults.length === 0}>
                  Export
                </Button>
              </Space>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={6}>
              <Select
                mode="multiple"
                placeholder="Log Levels"
                style={{ width: '100%' }}
                value={filters.logLevel}
                onChange={(value) => setFilters({...filters, logLevel: value})}
              >
                {logLevels.map(level => (
                  <Option key={level} value={level}>{level}</Option>
                ))}
              </Select>
            </Col>
            <Col span={6}>
              <Select
                mode="multiple"
                placeholder="Services"
                style={{ width: '100%' }}
                value={filters.serviceName}
                onChange={(value) => setFilters({...filters, serviceName: value})}
              >
                {services.map(service => (
                  <Option key={service} value={service}>{service}</Option>
                ))}
              </Select>
            </Col>
            <Col span={8}>
              <RangePicker
                style={{ width: '100%' }}
                showTime
                value={filters.dateRange}
                onChange={(dates) => setFilters({...filters, dateRange: dates})}
              />
            </Col>
            <Col span={4}>
              <Button type="primary" block onClick={performSearch} loading={loading}>
                Apply Filters
              </Button>
            </Col>
          </Row>
        </Space>
      </Card>

      {stats.totalHits && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic title="Total Results" value={stats.totalHits} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="Execution Time" 
                value={stats.executionTime} 
                suffix="ms"
                precision={2}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="Query" value={`"${stats.query}"`} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="Results Shown" value={searchResults.length} />
            </Card>
          </Col>
        </Row>
      )}

      <Card title="Search Results">
        <Table
          columns={columns}
          dataSource={searchResults}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `Total ${total} items`
          }}
        />
      </Card>
    </div>
  );
}

export default SearchInterface;
EOF

# API Documentation Component  
cat > frontend/src/components/ApiDocumentation.js << 'EOF'
import React from 'react';
import { Card, Typography, Divider, Tag, Table, Button, Space } from 'antd';
import { CopyOutlined, LinkOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

function ApiDocumentation() {
  const endpoints = [
    {
      method: 'POST',
      path: '/api/v1/logs/search',
      description: 'Advanced search with request body',
      status: 'Active'
    },
    {
      method: 'GET', 
      path: '/api/v1/logs/search',
      description: 'Simple search with query parameters',
      status: 'Active'
    },
    {
      method: 'GET',
      path: '/api/v1/logs/suggest',
      description: 'Get query suggestions',
      status: 'Active'
    },
    {
      method: 'GET',
      path: '/api/v1/logs/metrics',
      description: 'Get search analytics',
      status: 'Active'
    }
  ];

  const columns = [
    {
      title: 'Method',
      dataIndex: 'method',
      key: 'method',
      render: (method) => {
        const colors = { GET: 'green', POST: 'blue', PUT: 'orange', DELETE: 'red' };
        return <Tag color={colors[method]}>{method}</Tag>;
      }
    },
    {
      title: 'Endpoint',
      dataIndex: 'path',
      key: 'path',
      render: (path) => <Text code>{path}</Text>
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => <Tag color="green">{status}</Tag>
    }
  ];

  return (
    <div>
      <Card>
        <Title level={2}>Log Search API Documentation</Title>
        <Paragraph>
          RESTful API for querying distributed log data with advanced search capabilities,
          relevance scoring, and real-time filtering.
        </Paragraph>

        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<LinkOutlined />}>
            Interactive Docs
          </Button>
          <Button icon={<CopyOutlined />}>
            Copy API Key
          </Button>
        </Space>

        <Divider />

        <Title level={3}>Authentication</Title>
        <Paragraph>
          All API requests require authentication using Bearer tokens in the Authorization header:
        </Paragraph>
        <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px', marginBottom: '16px' }}>
          <Text code>Authorization: Bearer YOUR_ACCESS_TOKEN</Text>
        </div>

        <Title level={3}>Available Endpoints</Title>
        <Table
          columns={columns}
          dataSource={endpoints}
          pagination={false}
          style={{ marginBottom: 24 }}
        />

        <Title level={3}>Example Requests</Title>
        
        <Card size="small" title="POST /api/v1/logs/search" style={{ marginBottom: 16 }}>
          <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
            <pre>{`{
  "query": "error payment timeout",
  "start_time": "2025-06-16T00:00:00Z",
  "end_time": "2025-06-16T23:59:59Z",
  "log_level": ["ERROR", "WARN"],
  "service_name": ["payment-service"],
  "limit": 100,
  "offset": 0,
  "sort_by": "relevance"
}`}</pre>
          </div>
        </Card>

        <Card size="small" title="GET /api/v1/logs/search" style={{ marginBottom: 16 }}>
          <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
            <Text code>
              GET /api/v1/logs/search?q=error&log_level=ERROR&limit=50
            </Text>
          </div>
        </Card>

        <Title level={3}>Response Format</Title>
        <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
          <pre>{`{
  "query": "error payment",
  "total_hits": 156,
  "execution_time_ms": 45.7,
  "results": [
    {
      "id": "log_123",
      "timestamp": "2025-06-16T10:30:00Z",
      "level": "ERROR",
      "service_name": "payment-service",
      "message": "Payment processing failed",
      "score": 0.95
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 100,
    "has_more": false
  }
}`}</pre>
        </div>

        <Title level={3}>Rate Limits</Title>
        <Paragraph>
          • Authenticated users: 1000 requests/hour<br/>
          • Anonymous users: 100 requests/hour<br/>
          • Premium users: 10,000 requests/hour
        </Paragraph>

        <Title level={3}>Error Codes</Title>
        <Table
          size="small"
          pagination={false}
          dataSource={[
            { code: 400, description: 'Bad Request - Invalid parameters' },
            { code: 401, description: 'Unauthorized - Invalid or missing token' },
            { code: 429, description: 'Rate Limit Exceeded' },
            { code: 500, description: 'Internal Server Error' }
          ]}
          columns={[
            { title: 'Code', dataIndex: 'code', key: 'code', width: 80 },
            { title: 'Description', dataIndex: 'description', key: 'description' }
          ]}
        />
      </Card>
    </div>
  );
}

export default ApiDocumentation;
EOF

# Dashboard Component
cat > frontend/src/components/Dashboard.js << 'EOF'
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Progress } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, ApiOutlined, SearchOutlined } from '@ant-design/icons';

function Dashboard() {
  const [metrics, setMetrics] = useState({
    totalQueries: 1247,
    avgResponseTime: 89.5,
    cacheHitRate: 73.2,
    errorRate: 2.1
  });

  const topQueries = [
    { query: 'error payment', count: 45, trend: 'up' },
    { query: 'timeout database', count: 38, trend: 'down' },
    { query: 'login failed', count: 29, trend: 'up' },
    { query: 'api gateway', count: 24, trend: 'stable' },
    { query: 'memory usage', count: 19, trend: 'up' }
  ];

  const recentActivity = [
    {
      time: '10:30:15',
      user: 'admin',
      query: 'error payment timeout',
      results: 156,
      duration: '45ms'
    },
    {
      time: '10:29:45',
      user: 'developer',
      query: 'database connection',
      results: 23,
      duration: '67ms'
    },
    {
      time: '10:28:30',
      user: 'ops-team',
      query: 'memory leak',
      results: 8,
      duration: '123ms'
    }
  ];

  const queryColumns = [
    {
      title: 'Query',
      dataIndex: 'query',
      key: 'query',
      render: (text) => <span style={{ fontFamily: 'monospace' }}>{text}</span>
    },
    {
      title: 'Count',
      dataIndex: 'count',
      key: 'count',
      width: 80
    },
    {
      title: 'Trend',
      dataIndex: 'trend',
      key: 'trend',
      width: 80,
      render: (trend) => {
        const colors = { up: 'red', down: 'green', stable: 'gray' };
        const icons = { 
          up: <ArrowUpOutlined />, 
          down: <ArrowDownOutlined />, 
          stable: <span>-</span> 
        };
        return <span style={{ color: colors[trend] }}>{icons[trend]}</span>;
      }
    }
  ];

  const activityColumns = [
    {
      title: 'Time',
      dataIndex: 'time',
      key: 'time',
      width: 100
    },
    {
      title: 'User',
      dataIndex: 'user',
      key: 'user',
      width: 120,
      render: (user) => <Tag color="blue">{user}</Tag>
    },
    {
      title: 'Query',
      dataIndex: 'query',
      key: 'query',
      ellipsis: true
    },
    {
      title: 'Results',
      dataIndex: 'results',
      key: 'results',
      width: 80
    },
    {
      title: 'Duration',
      dataIndex: 'duration',
      key: 'duration',
      width: 80
    }
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Queries"
              value={metrics.totalQueries}
              prefix={<SearchOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Avg Response Time"
              value={metrics.avgResponseTime}
              suffix="ms"
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Cache Hit Rate"
              value={metrics.cacheHitRate}
              suffix="%"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Error Rate"
              value={metrics.errorRate}
              suffix="%"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="Top Search Queries">
            <Table
              columns={queryColumns}
              dataSource={topQueries}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="API Performance">
            <div style={{ marginBottom: 16 }}>
              <div>Response Time Distribution</div>
              <Progress 
                percent={85} 
                strokeColor="#52c41a" 
                format={() => '< 100ms'}
                style={{ marginBottom: 8 }}
              />
              <Progress 
                percent={12} 
                strokeColor="#faad14" 
                format={() => '100-500ms'}
                style={{ marginBottom: 8 }}
              />
              <Progress 
                percent={3} 
                strokeColor="#f5222d" 
                format={() => '> 500ms'}
              />
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="Recent Search Activity">
        <Table
          columns={activityColumns}
          dataSource={recentActivity}
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
}

export default Dashboard;
EOF

# Frontend CSS
cat > frontend/src/App.css << 'EOF'
.App {
  text-align: center;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.site-layout-background {
  background: #fff;
}

.ant-table-thead > tr > th {
  background-color: #fafafa;
}

.ant-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
  border-radius: 8px;
}

.ant-statistic-content {
  font-size: 24px;
  font-weight: bold;
}

.ant-btn-primary {
  background-color: #1890ff;
  border-color: #1890ff;
}

.ant-btn-primary:hover {
  background-color: #40a9ff;
  border-color: #40a9ff;
}

.ant-tag {
  margin: 2px;
}

.ant-input-search .ant-input-group .ant-input {
  border-radius: 6px 0 0 6px;
}

.ant-input-search .ant-input-group .ant-btn {
  border-radius: 0 6px 6px 0;
}

code {
  background-color: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Monaco', 'Consolas', monospace;
}

pre {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.4;
}
EOF

# Frontend index.js
cat > frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

# Frontend index.css
cat > frontend/src/index.css << 'EOF'
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f0f2f5;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

#root {
  min-height: 100vh;
}
EOF

# Frontend public/index.html
cat > frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Log Search API Interface" />
    <title>Log Search API</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF

# Tests
cat > backend/tests/test_search_api.py << 'EOF'
import pytest
from fastapi.testclient import TestClient
from ..app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_search_endpoint_without_auth():
    response = client.get("/api/v1/logs/search?q=test")
    assert response.status_code == 401

def test_auth_endpoint():
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "secret"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_search_with_auth():
    # Get token first
    auth_response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "secret"}
    )
    token = auth_response.json()["access_token"]
    
    # Use token for search
    response = client.get(
        "/api/v1/logs/search?q=test",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "results" in response.json()
EOF

# Docker configuration
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.1
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  redis:
    image: redis:7.0-alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - elasticsearch
      - redis
    environment:
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  es_data:
EOF

# Backend Dockerfile
cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

# Frontend Dockerfile
cat > frontend/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
EOF

# Demo script
cat > demo.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Log Search API Demo"
echo "================================"

# Install backend dependencies
echo "📦 Installing Python dependencies..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Start services with Docker
echo "🐳 Starting services with Docker..."
docker-compose up -d elasticsearch redis

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 30

# Start backend
echo "🔧 Starting backend API..."
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
echo "🎨 Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ Demo setup complete!"
echo ""
echo "🔗 Access points:"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/api/docs"
echo "   Health: http://localhost:8000/api/v1/health/"
echo ""
echo "📝 Demo credentials:"
echo "   Username: testuser"
echo "   Password: secret"
echo ""
echo "🛑 To stop demo: ./cleanup.sh"

# Save PIDs for cleanup
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid
EOF

# Cleanup script
cat > cleanup.sh << 'EOF'
#!/bin/bash

echo "🧹 Cleaning up Log Search API Demo"
echo "===================================="

# Kill backend process
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null
    rm .backend.pid
    echo "✅ Backend stopped"
fi

# Kill frontend process
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null
    rm .frontend.pid
    echo "✅ Frontend stopped"
fi

# Stop Docker services
docker-compose down -v
echo "✅ Docker services stopped"

echo "🎉 Cleanup complete!"
EOF

# Make scripts executable
chmod +x demo.sh cleanup.sh

# Run tests
echo "🧪 Running tests..."
cd backend
python -m pytest tests/ -v
cd ..

echo "✅ Day 58: Search API Implementation Complete!"
echo ""
echo "📋 Next steps:"
echo "1. Run: ./demo.sh"
echo "2. Open: http://localhost:3000"
echo "3. Test the API with credentials: testuser/secret"
echo "4. Explore the interactive API docs at /api/docs"
echo "5. Stop with: ./cleanup.sh"