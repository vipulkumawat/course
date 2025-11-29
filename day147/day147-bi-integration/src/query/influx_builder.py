from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time
from src.models import MetricQuery, BIDataResponse, MetricType
from config.settings import settings

class InfluxQueryBuilder:
    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG
        )
        self.query_api = self.client.query_api()
    
    def build_flux_query(self, query: MetricQuery) -> str:
        """Build Flux query for InfluxDB"""
        start_str = query.time_range.start.isoformat()
        end_str = query.time_range.end.isoformat()
        
        flux_query = f'''
        from(bucket: "{settings.INFLUXDB_BUCKET}")
          |> range(start: {start_str}, stop: {end_str})
          |> filter(fn: (r) => r["_measurement"] == "{query.measurement}")
        '''
        
        # Add tag filters
        for tag_key, tag_values in query.filters.items():
            if tag_values:
                value_filter = ' or '.join([f'r["{tag_key}"] == "{v}"' for v in tag_values])
                flux_query += f'\n  |> filter(fn: (r) => {value_filter})'
        
        # Aggregation
        window = query.aggregation_window.value
        flux_query += f'\n  |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)'
        flux_query += '\n  |> yield(name: "mean")'
        
        return flux_query
    
    def execute_query(self, query: MetricQuery) -> BIDataResponse:
        """Execute query and return BI-friendly response"""
        start_time = time.time()
        
        try:
            flux_query = self.build_flux_query(query)
            result = self.query_api.query(flux_query, org=settings.INFLUXDB_ORG)
            
            # Transform to tabular format
            data = []
            for table in result:
                for record in table.records:
                    row = {
                        "timestamp": record.get_time().isoformat(),
                        "time": record.get_time().isoformat(),  # Also include 'time' for compatibility
                        "service": record.values.get("service", "unknown"),
                        "endpoint": record.values.get("endpoint", "unknown"),
                        "value": record.get_value()
                    }
                    data.append(row)
        except Exception as e:
            # Return empty response on error
            import logging
            logging.error(f"InfluxDB query error: {e}")
            data = []
        
        # Apply pagination
        start_idx = (query.page - 1) * query.page_size
        end_idx = start_idx + query.page_size
        paginated_data = data[start_idx:end_idx]
        
        query_time_ms = (time.time() - start_time) * 1000
        
        schema = {
            "timestamp": "datetime",
            "time": "datetime",
            "service": "string",
            "endpoint": "string",
            "value": "float"
        }
        
        return BIDataResponse(
            schema=schema,
            data=paginated_data,
            total_rows=len(data),
            page=query.page,
            page_size=query.page_size,
            query_time_ms=query_time_ms,
            cached=False
        )
    
    def get_available_services(self) -> List[str]:
        """Get list of available services from InfluxDB"""
        try:
            flux_query = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
              |> range(start: -30d)
              |> filter(fn: (r) => r["_measurement"] == "http_requests")
              |> keep(columns: ["service"])
              |> distinct(column: "service")
            '''
            
            result = self.query_api.query(flux_query, org=settings.INFLUXDB_ORG)
            services = []
            for table in result:
                for record in table.records:
                    service = record.values.get("service")
                    if service:
                        services.append(service)
            return list(set(services)) if services else ["api", "web", "database"]  # Default services
        except Exception as e:
            import logging
            logging.error(f"Error getting available services: {e}")
            # Return default services if query fails
            return ["api", "web", "database"]
