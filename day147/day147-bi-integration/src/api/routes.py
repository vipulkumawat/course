from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from src.models import *
from src.auth.oauth import get_current_user, check_permission, filter_by_allowed_services, TokenData
from src.query.influx_builder import InfluxQueryBuilder
from src.query.cache import CacheLayer
from src.export.generator import ExportGenerator

router = APIRouter()
query_builder = InfluxQueryBuilder()
cache_layer = CacheLayer()
export_generator = ExportGenerator()

@router.get("/metrics/schema", response_model=SchemaResponse)
async def get_schema(current_user: TokenData = Depends(get_current_user)):
    """Get available metrics and dimensions"""
    check_permission(current_user, "read:metrics")
    
    services = query_builder.get_available_services()
    allowed_services = filter_by_allowed_services(current_user, services)
    
    metrics = [
        MetricSchema(
            name="request_count",
            display_name="Request Count",
            data_type="integer",
            description="Total number of requests",
            unit="requests"
        ),
        MetricSchema(
            name="avg_response_time",
            display_name="Average Response Time",
            data_type="float",
            description="Average response time",
            unit="milliseconds"
        ),
        MetricSchema(
            name="error_rate",
            display_name="Error Rate",
            data_type="float",
            description="Percentage of requests with errors",
            unit="percentage"
        )
    ]
    
    dimensions = [
        DimensionSchema(
            name="service",
            display_name="Service",
            values=allowed_services,
            filterable=True
        ),
        DimensionSchema(
            name="endpoint",
            display_name="API Endpoint",
            values=["/api/users", "/api/orders", "/api/products"],
            filterable=True
        )
    ]
    
    return SchemaResponse(
        metrics=metrics,
        dimensions=dimensions,
        time_range_available=TimeRange(
            start=datetime.utcnow() - timedelta(days=90),
            end=datetime.utcnow()
        )
    )

@router.post("/metrics/timeseries", response_model=BIDataResponse)
async def query_timeseries(
    query: MetricQuery,
    current_user: TokenData = Depends(get_current_user)
):
    """Query time series metrics"""
    check_permission(current_user, "read:metrics")
    
    # Filter services by user permissions
    if "service" in query.filters:
        query.filters["service"] = filter_by_allowed_services(
            current_user, 
            query.filters["service"]
        )
    
    # Check cache
    cache_key = cache_layer.generate_cache_key(query, current_user.allowed_services)
    cached_response = cache_layer.get(cache_key)
    if cached_response:
        cached_response.cached = True
        return cached_response
    
    # Execute query
    response = query_builder.execute_query(query)
    
    # Cache result
    cache_layer.set(cache_key, response)
    
    return response

@router.post("/metrics/aggregate")
async def query_aggregate(
    measurement: str = Query("http_requests"),
    start: datetime = Query(...),
    end: datetime = Query(...),
    group_by: List[str] = Query(default=["service"]),
    current_user: TokenData = Depends(get_current_user)
):
    """Get pre-aggregated metrics"""
    check_permission(current_user, "read:metrics")
    
    # Simplified aggregation - in production, use materialized views
    query = MetricQuery(
        measurement=measurement,
        time_range=TimeRange(start=start, end=end),
        aggregation_window=AggregationWindow.DAY,
        page_size=10000
    )
    
    response = query_builder.execute_query(query)
    
    # Group by requested dimensions
    import pandas as pd
    df = pd.DataFrame(response.data)
    if not df.empty and group_by:
        aggregated = df.groupby(group_by).agg({
            'value': ['sum', 'mean', 'count']
        }).reset_index()
        response.data = aggregated.to_dict('records')
    
    return response

@router.post("/exports/generate", response_model=ExportMetadata)
async def generate_export(
    request: ExportRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Generate data export"""
    check_permission(current_user, "write:exports")
    
    # Filter services by user permissions
    if request.services:
        request.services = filter_by_allowed_services(current_user, request.services)
    
    try:
        metadata = export_generator.generate_export(request)
        return metadata
    except Exception as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate export: {str(e)}"
        )

@router.get("/exports/manifest")
async def get_export_manifest(
    current_user: TokenData = Depends(get_current_user)
):
    """Get export manifest"""
    check_permission(current_user, "read:exports")
    manifest = export_generator.get_manifest()
    # Return exports list directly for easier frontend consumption
    return manifest.get("exports", [])
