import time
from typing import Dict, List
from ..models.search_request import SearchRequest, SearchResponse
from ..services.facet_engine import FacetEngine

class SearchService:
    def __init__(self, facet_engine: FacetEngine):
        self.facet_engine = facet_engine
        
    async def search(self, search_request: SearchRequest) -> SearchResponse:
        """Perform faceted search on logs"""
        start_time = time.time()
        
        # Get filtered logs
        logs = await self.facet_engine.search_logs(search_request)
        
        # Get facets with current filters applied
        facets_summary = await self.facet_engine.get_facets(search_request.filters)
        
        query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return SearchResponse(
            logs=logs,
            total_count=facets_summary.total_logs,
            facets=[facet.dict() for facet in facets_summary.facets],
            query_time_ms=round(query_time, 2),
            applied_filters=search_request.filters
        )
