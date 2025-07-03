from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Set
import redis
import json
import uvicorn
import re

class SearchRequest(BaseModel):
    terms: List[str]

class IndexNode:
    def __init__(self, node_id: str, port: int, redis_host: str = "localhost"):
        self.node_id = node_id
        self.port = port
        self.app = FastAPI(title=f"Index Node {node_id}")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins for demo
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.redis_client = redis.Redis(host=redis_host, decode_responses=True)
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.post("/search")
        async def search(request: SearchRequest):
            try:
                results = self.search_terms(request.terms)
                return {"documents": results, "node_id": self.node_id}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/index")
        async def index_document(doc_id: str, content: str):
            try:
                self.add_document(doc_id, content)
                return {"status": "indexed", "doc_id": doc_id, "node_id": self.node_id}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy", "node_id": self.node_id}
        
        @self.app.get("/stats")
        async def stats():
            term_count = len(self.redis_client.keys(f"term:{self.node_id}:*"))
            doc_count = len(self.redis_client.keys(f"doc:{self.node_id}:*"))
            return {
                "node_id": self.node_id,
                "term_count": term_count,
                "document_count": doc_count,
                "status": "active"
            }
    
    def add_document(self, doc_id: str, content: str):
        doc_key = f"doc:{self.node_id}:{doc_id}"
        self.redis_client.set(doc_key, content)
        
        terms = self._extract_terms(content)
        for term in terms:
            term_key = f"term:{self.node_id}:{term}"
            self.redis_client.sadd(term_key, doc_id)
    
    def search_terms(self, terms: List[str]) -> List[Dict]:
        if not terms:
            return []
        
        doc_sets = []
        for term in terms:
            term_key = f"term:{self.node_id}:{term}"
            doc_ids = self.redis_client.smembers(term_key)
            doc_sets.append(set(doc_ids))
        
        if doc_sets:
            common_docs = doc_sets[0]
            for doc_set in doc_sets[1:]:
                common_docs = common_docs.intersection(doc_set)
        else:
            common_docs = set()
        
        results = []
        for doc_id in common_docs:
            doc_key = f"doc:{self.node_id}:{doc_id}"
            content = self.redis_client.get(doc_key)
            
            if content:
                score = self._calculate_score(content, terms)
                results.append({
                    "id": doc_id,
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "score": score,
                    "node": self.node_id
                })
        
        return results
    
    def _extract_terms(self, content: str) -> Set[str]:
        terms = re.findall(r'\b\w+\b', content.lower())
        return set(terms)
    
    def _calculate_score(self, content: str, query_terms: List[str]) -> float:
        content_terms = self._extract_terms(content)
        matches = sum(1 for term in query_terms if term in content_terms)
        return matches / len(query_terms) if query_terms else 0.0
    
    def start(self):
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
