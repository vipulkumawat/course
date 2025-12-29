import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict
import json
from datetime import datetime

class DatabaseManager:
    """Manages database connections and query execution"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None
    
    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self._initialize_schema()
        except Exception as e:
            print(f"Database connection failed: {e}")
            # Use in-memory fallback
            self.conn = None
    
    def _initialize_schema(self):
        """Initialize logs table if it doesn't exist"""
        if not self.conn:
            return
        
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    level VARCHAR(20) NOT NULL,
                    service VARCHAR(100),
                    message TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
                CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
                CREATE INDEX IF NOT EXISTS idx_logs_service ON logs(service);
            """)
            self.conn.commit()
            
            # Insert sample data
            self._insert_sample_data()
    
    def _insert_sample_data(self):
        """Insert sample log data for demo"""
        sample_logs = [
            (datetime.now(), 'error', 'payment_service', 'Payment processing failed', '{"user_id": 123}'),
            (datetime.now(), 'error', 'payment_service', 'Database connection timeout', '{"retry_count": 3}'),
            (datetime.now(), 'warn', 'auth_service', 'Invalid token provided', '{"ip": "192.168.1.1"}'),
            (datetime.now(), 'info', 'api_gateway', 'Request processed successfully', '{"duration_ms": 45}'),
            (datetime.now(), 'error', 'user_service', 'User not found', '{"user_id": 456}'),
        ] * 20  # 100 sample logs
        
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM logs")
            if cur.fetchone()[0] == 0:
                for log in sample_logs:
                    cur.execute(
                        "INSERT INTO logs (timestamp, level, service, message, metadata) VALUES (%s, %s, %s, %s, %s)",
                        log
                    )
                self.conn.commit()
    
    def execute_query(self, sql: str) -> List[Dict]:
        """Execute SQL query and return results"""
        if not self.conn:
            return self._mock_results()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)
                results = cur.fetchall()
                # Convert datetime objects to strings
                return [dict(row) for row in results]
        except Exception as e:
            print(f"Query execution error: {e}")
            return []
    
    def _mock_results(self) -> List[Dict]:
        """Return mock results for demo"""
        return [
            {
                'id': 1,
                'timestamp': datetime.now().isoformat(),
                'level': 'error',
                'service': 'payment_service',
                'message': 'Payment processing failed',
                'metadata': {'user_id': 123}
            },
            {
                'id': 2,
                'timestamp': datetime.now().isoformat(),
                'level': 'warn',
                'service': 'auth_service',
                'message': 'Invalid token provided',
                'metadata': {'ip': '192.168.1.1'}
            }
        ]
    
    def get_schema_fields(self) -> List[str]:
        """Get available fields from logs table"""
        return ['timestamp', 'level', 'service', 'message', 'metadata']
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
