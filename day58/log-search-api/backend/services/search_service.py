import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from elasticsearch import Elasticsearch
import redis
from schemas.search import SearchRequest, SearchResponse, LogEntry, LogLevel

class SearchService:
    def __init__(self):
        self.es = Elasticsearch([{"host": "localhost", "port": 9200, "scheme": "http"}])
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
