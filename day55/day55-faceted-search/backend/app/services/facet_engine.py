import redis
import json
import sqlite3
from typing import Dict, List, Any
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import asyncio
import logging
from ..models.facet import Facet, FacetValue, FacetSummary
from ..models.log_entry import LogEntry

logger = logging.getLogger(__name__)

class FacetEngine:
    def __init__(self, redis_url: str = "redis://localhost:6379", db_path: str = "data/logs.db"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.db_path = db_path
        self.facet_definitions = {
            'service': {'type': 'categorical', 'display': 'Service'},
            'level': {'type': 'categorical', 'display': 'Log Level'},
            'region': {'type': 'categorical', 'display': 'Region'},
            'response_time_range': {'type': 'numeric', 'display': 'Response Time'},
            'hour_of_day': {'type': 'temporal', 'display': 'Time of Day'}
        }
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for log storage"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                service TEXT,
                level TEXT,
                message TEXT,
                metadata TEXT,
                source_ip TEXT,
                request_id TEXT,
                region TEXT,
                response_time INTEGER
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_service ON logs(service)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_level ON logs(level)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp)')
        conn.commit()
        conn.close()
        
    async def extract_facets(self, log_entry: LogEntry) -> Dict[str, str]:
        """Extract facet values from a log entry"""
        facets = {}
        
        # Direct categorical facets
        facets['service'] = log_entry.service
        facets['level'] = log_entry.level
        facets['region'] = log_entry.region or 'unknown'
        
        # Numeric range facets
        if log_entry.response_time:
            if log_entry.response_time < 100:
                facets['response_time_range'] = '0-100ms'
            elif log_entry.response_time < 500:
                facets['response_time_range'] = '100-500ms'
            elif log_entry.response_time < 1000:
                facets['response_time_range'] = '500ms-1s'
            else:
                facets['response_time_range'] = '1s+'
        else:
            facets['response_time_range'] = 'unknown'
            
        # Temporal facets
        hour = log_entry.timestamp.hour
        if 6 <= hour < 12:
            facets['hour_of_day'] = 'morning'
        elif 12 <= hour < 18:
            facets['hour_of_day'] = 'afternoon'
        elif 18 <= hour < 22:
            facets['hour_of_day'] = 'evening'
        else:
            facets['hour_of_day'] = 'night'
            
        return facets
        
    async def index_log(self, log_entry: LogEntry):
        """Index a log entry and update facet counts"""
        # Store in SQLite
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT OR REPLACE INTO logs 
            (id, timestamp, service, level, message, metadata, source_ip, request_id, region, response_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_entry.id,
            log_entry.timestamp.isoformat(),
            log_entry.service,
            log_entry.level,
            log_entry.message,
            json.dumps(log_entry.metadata),
            log_entry.source_ip,
            log_entry.request_id,
            log_entry.region,
            log_entry.response_time
        ))
        conn.commit()
        conn.close()
        
        # Extract and update facets in Redis
        facets = await self.extract_facets(log_entry)
        pipe = self.redis_client.pipeline()
        
        for facet_name, value in facets.items():
            pipe.hincrby(f"facet:{facet_name}", value, 1)
            pipe.hincrby("facet:total", facet_name, 1)
            
        pipe.execute()
        logger.info(f"Indexed log {log_entry.id} with facets: {facets}")
        
    async def get_facets(self, applied_filters: Dict[str, List[str]] = None) -> FacetSummary:
        """Get all facets with counts, optionally filtered"""
        applied_filters = applied_filters or {}
        facets = []
        
        # Build SQL query with filters
        where_conditions = []
        params = []
        
        for facet_name, values in applied_filters.items():
            if values and facet_name in ['service', 'level', 'region']:
                placeholders = ','.join(['?' for _ in values])
                where_conditions.append(f"{facet_name} IN ({placeholders})")
                params.extend(values)
                
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        conn = sqlite3.connect(self.db_path)
        
        # Get total count
        total_query = f"SELECT COUNT(*) FROM logs {where_clause}"
        total_count = conn.execute(total_query, params).fetchone()[0]
        
        # Get facet counts
        for facet_name, config in self.facet_definitions.items():
            if facet_name == 'response_time_range':
                # Handle numeric ranges
                query = f'''
                    SELECT 
                        CASE 
                            WHEN response_time < 100 THEN '0-100ms'
                            WHEN response_time < 500 THEN '100-500ms'
                            WHEN response_time < 1000 THEN '500ms-1s'
                            ELSE '1s+'
                        END as range_value,
                        COUNT(*) as count
                    FROM logs {where_clause}
                    GROUP BY range_value
                '''
            elif facet_name == 'hour_of_day':
                # Handle temporal ranges
                query = f'''
                    SELECT 
                        CASE 
                            WHEN CAST(substr(timestamp, 12, 2) AS INTEGER) BETWEEN 6 AND 11 THEN 'morning'
                            WHEN CAST(substr(timestamp, 12, 2) AS INTEGER) BETWEEN 12 AND 17 THEN 'afternoon'
                            WHEN CAST(substr(timestamp, 12, 2) AS INTEGER) BETWEEN 18 AND 21 THEN 'evening'
                            ELSE 'night'
                        END as time_range,
                        COUNT(*) as count
                    FROM logs {where_clause}
                    GROUP BY time_range
                '''
            else:
                # Handle categorical facets
                query = f"SELECT {facet_name}, COUNT(*) FROM logs {where_clause} GROUP BY {facet_name}"
            
            cursor = conn.execute(query, params)
            results = cursor.fetchall()
            
            facet_values = []
            for value, count in results:
                if value:  # Skip null values
                    facet_values.append(FacetValue(
                        value=str(value),
                        count=count,
                        selected=str(value) in applied_filters.get(facet_name, [])
                    ))
            
            facets.append(Facet(
                name=facet_name,
                display_name=config['display'],
                values=sorted(facet_values, key=lambda x: x.count, reverse=True),
                facet_type=config['type']
            ))
            
        conn.close()
        
        return FacetSummary(
            total_logs=total_count,
            facets=facets,
            applied_filters=applied_filters
        )
        
    async def search_logs(self, search_request) -> List[Dict]:
        """Search logs with faceted filters"""
        where_conditions = []
        params = []
        
        # Add text search
        if search_request.query:
            where_conditions.append("message LIKE ?")
            params.append(f"%{search_request.query}%")
            
        # Add facet filters
        for facet_name, values in search_request.filters.items():
            if values and facet_name in ['service', 'level', 'region']:
                placeholders = ','.join(['?' for _ in values])
                where_conditions.append(f"{facet_name} IN ({placeholders})")
                params.extend(values)
                
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        query = f'''
            SELECT id, timestamp, service, level, message, metadata, source_ip, request_id, region, response_time
            FROM logs {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        '''
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(query, params + [search_request.limit, search_request.offset])
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0],
                'timestamp': row[1],
                'service': row[2],
                'level': row[3],
                'message': row[4],
                'metadata': json.loads(row[5]) if row[5] else {},
                'source_ip': row[6],
                'request_id': row[7],
                'region': row[8],
                'response_time': row[9]
            })
            
        conn.close()
        return logs
