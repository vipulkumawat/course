#!/usr/bin/env python3
"""
Distributed Search Coordinator
Coordinates search operations across multiple index nodes using consistent hashing.
"""

import asyncio
import json
import sys
import time
import os
from typing import Dict, List, Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import redis

# Add the src directory to the path to import hash_ring
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from coordinator.hash_ring import ConsistentHashRing

class SearchRequest(BaseModel):
    terms: List[str]

class IndexRequest(BaseModel):
    doc_id: str
    content: str

class SearchResponse(BaseModel):
    documents: List[Dict]
    total_results: int
    search_time_ms: float
    nodes_queried: List[str]

class Coordinator:
    def __init__(self, port: int = 8000):
        self.port = port
        self.app = FastAPI(title="Distributed Search Coordinator")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins for demo
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.nodes = ['node-1', 'node-2', 'node-3', 'node-4']
        self.node_ports = [8101, 8102, 8103, 8104]
        self.hash_ring = ConsistentHashRing(self.nodes)
        self.redis_client = redis.Redis(host='localhost', decode_responses=True)
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.get("/")
        async def root():
            return {
                "service": "Distributed Search Coordinator",
                "status": "running",
                "nodes": self.nodes,
                "hash_ring": "active"
            }
        
        @self.app.get("/health")
        async def health():
            # Check health of all nodes
            node_health = {}
            async with httpx.AsyncClient() as client:
                for i, node in enumerate(self.nodes):
                    port = self.node_ports[i]
                    try:
                        response = await client.get(f"http://localhost:{port}/health", timeout=2.0)
                        node_health[node] = response.status_code == 200
                    except:
                        node_health[node] = False
            
            healthy_nodes = sum(node_health.values())
            return {
                "status": "healthy" if healthy_nodes > 0 else "degraded",
                "coordinator_port": self.port,
                "nodes": node_health,
                "healthy_nodes": healthy_nodes,
                "total_nodes": len(self.nodes)
            }
        
        @self.app.post("/search")
        async def distributed_search(request: SearchRequest):
            """Coordinate search across all nodes"""
            start_time = time.time()
            
            if not request.terms:
                return SearchResponse(
                    documents=[],
                    total_results=0,
                    search_time_ms=0,
                    nodes_queried=[]
                )
            
            # Search all nodes in parallel
            all_results = []
            nodes_queried = []
            
            async with httpx.AsyncClient() as client:
                tasks = []
                for i, node in enumerate(self.nodes):
                    port = self.node_ports[i]
                    task = self._search_node(client, port, request.terms, node)
                    tasks.append(task)
                
                # Wait for all nodes to respond
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    node = self.nodes[i]
                    if isinstance(result, Exception):
                        print(f"Error querying {node}: {result}")
                        continue
                    
                    nodes_queried.append(node)
                    if result and 'documents' in result:
                        all_results.extend(result['documents'])
            
            # Remove duplicates based on document ID
            seen_ids = set()
            unique_results = []
            for doc in all_results:
                if doc['id'] not in seen_ids:
                    seen_ids.add(doc['id'])
                    unique_results.append(doc)
            
            # Sort by score (highest first)
            unique_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            search_time = (time.time() - start_time) * 1000
            
            return SearchResponse(
                documents=unique_results,
                total_results=len(unique_results),
                search_time_ms=round(search_time, 2),
                nodes_queried=nodes_queried
            )
        
        @self.app.post("/index")
        async def distributed_index(request: IndexRequest):
            """Index document using hash ring to determine target node"""
            # Use hash ring to determine which node should handle this document
            target_node = self.hash_ring.get_node(request.doc_id)
            
            if not target_node:
                raise HTTPException(status_code=500, detail="No available nodes")
            
            # Find the port for the target node
            node_index = self.nodes.index(target_node)
            target_port = self.node_ports[node_index]
            
            # Index the document on the target node
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"http://localhost:{target_port}/index",
                        params={"doc_id": request.doc_id, "content": request.content},
                        timeout=5.0
                    )
                    
                    if response.status_code == 200:
                        return {
                            "status": "indexed",
                            "doc_id": request.doc_id,
                            "target_node": target_node,
                            "coordinator": "coordinator-1"
                        }
                    else:
                        raise HTTPException(status_code=response.status_code, detail="Indexing failed")
                        
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Indexing error: {str(e)}")
        
        @self.app.get("/stats")
        async def coordinator_stats():
            """Get coordinator and node statistics"""
            # Get stats from all nodes
            node_stats = {}
            total_docs = 0
            total_terms = 0
            
            async with httpx.AsyncClient() as client:
                for i, node in enumerate(self.nodes):
                    port = self.node_ports[i]
                    try:
                        response = await client.get(f"http://localhost:{port}/stats", timeout=2.0)
                        if response.status_code == 200:
                            stats = response.json()
                            node_stats[node] = stats
                            total_docs += stats.get('document_count', 0)
                            total_terms += stats.get('term_count', 0)
                        else:
                            node_stats[node] = {"error": "Failed to get stats"}
                    except:
                        node_stats[node] = {"error": "Node unreachable"}
            
            return {
                "coordinator": {
                    "port": self.port,
                    "status": "active",
                    "hash_ring_nodes": len(self.nodes)
                },
                "cluster": {
                    "total_documents": total_docs,
                    "total_terms": total_terms,
                    "active_nodes": len([s for s in node_stats.values() if 'error' not in s])
                },
                "nodes": node_stats
            }
        
        @self.app.get("/hash-distribution")
        async def hash_distribution():
            """Show hash ring distribution"""
            # Test distribution with sample terms
            test_terms = [
                "error", "login", "database", "payment", "security",
                "user", "system", "api", "network", "authentication"
            ]
            
            distribution = {}
            for term in test_terms:
                node = self.hash_ring.get_node(term)
                distribution[term] = node
            
            return {
                "hash_ring": {
                    "nodes": self.nodes,
                    "virtual_nodes": 100
                },
                "sample_distribution": distribution,
                "distribution_summary": {
                    term: node for term, node in distribution.items()
                }
            }
    
    async def _search_node(self, client: httpx.AsyncClient, port: int, terms: List[str], node_id: str):
        """Search a single node"""
        try:
            response = await client.post(
                f"http://localhost:{port}/search",
                json={"terms": terms},
                timeout=5.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Node {node_id} returned status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error searching node {node_id}: {e}")
            return None
    
    def start(self):
        """Start the coordinator server"""
        print(f"🚀 Starting Distributed Search Coordinator on port {self.port}")
        print(f"📡 Coordinating nodes: {', '.join(self.nodes)}")
        print(f"🔗 Hash ring: {len(self.nodes)} nodes with 100 virtual nodes each")
        print(f"🌐 Coordinator URL: http://localhost:{self.port}")
        print("=" * 60)
        
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)

def main():
    """Main entry point"""
    coordinator = Coordinator(port=8000)
    coordinator.start()

if __name__ == "__main__":
    main() 