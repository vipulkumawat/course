#!/usr/bin/env python3
"""Populate sample metrics data into InfluxDB for dashboard demonstration"""
import sys
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from config.settings import settings

def populate_sample_data():
    """Populate sample HTTP request metrics"""
    client = InfluxDBClient(
        url=settings.INFLUXDB_URL,
        token=settings.INFLUXDB_TOKEN,
        org=settings.INFLUXDB_ORG
    )
    
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    # Generate data for last 24 hours
    now = datetime.utcnow()
    services = ["api", "web", "database"]
    endpoints = ["/api/users", "/api/orders", "/api/products", "/api/health"]
    
    points = []
    for hour_offset in range(24):
        timestamp = now - timedelta(hours=hour_offset)
        for service in services:
            for endpoint in endpoints:
                # Generate realistic metrics
                response_time = 50 + (hour_offset % 10) * 10  # 50-140ms
                request_count = 100 + (hour_offset % 5) * 50  # 100-350 requests
                error_count = max(0, int(request_count * 0.02))  # 2% error rate
                
                # Write response time
                point = Point("http_requests") \
                    .tag("service", service) \
                    .tag("endpoint", endpoint) \
                    .tag("status", "200") \
                    .field("response_time_ms", response_time) \
                    .field("request_count", request_count) \
                    .field("error_count", error_count) \
                    .time(timestamp)
                points.append(point)
    
    # Write all points
    write_api.write(bucket=settings.INFLUXDB_BUCKET, org=settings.INFLUXDB_ORG, record=points)
    print(f"✅ Populated {len(points)} data points into InfluxDB")
    print(f"   Time range: {(now - timedelta(hours=23)).isoformat()} to {now.isoformat()}")
    print(f"   Services: {', '.join(services)}")
    print(f"   Endpoints: {', '.join(endpoints)}")
    
    client.close()

if __name__ == "__main__":
    try:
        populate_sample_data()
    except Exception as e:
        print(f"❌ Error populating data: {e}")
        sys.exit(1)

