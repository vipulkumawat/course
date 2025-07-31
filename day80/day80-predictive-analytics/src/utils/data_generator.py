#!/usr/bin/env python3
"""Generate sample log data for training and testing"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import redis
import sys
# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.config import config

class LogDataGenerator:
    """Generate realistic log data for training models"""
    
    def __init__(self):
        self.redis_client = redis.from_url(config.redis_url)
        
    def generate_web_server_logs(self, days: int = 7, samples_per_hour: int = 12) -> pd.DataFrame:
        """Generate realistic web server response time logs"""
        
        # Time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Generate timestamps (every 5 minutes)
        timestamps = pd.date_range(start=start_time, end=end_time, freq='5T')
        
        data = []
        for ts in timestamps:
            # Create realistic patterns
            hour = ts.hour
            day_of_week = ts.weekday()
            
            # Base response time with daily and weekly patterns
            base_response = 50.0  # Base 50ms
            
            # Daily pattern (higher during business hours)
            if 9 <= hour <= 17:
                base_response *= 1.5
            elif 18 <= hour <= 22:
                base_response *= 1.2
            
            # Weekly pattern (higher on weekdays)
            if day_of_week < 5:  # Weekdays
                base_response *= 1.3
            
            # Add noise and occasional spikes
            noise = np.random.normal(0, base_response * 0.1)
            spike = 0
            
            # Random spikes (5% probability)
            if np.random.random() < 0.05:
                spike = base_response * np.random.uniform(2, 5)
            
            response_time = max(10.0, base_response + noise + spike)
            
            # Create log entry
            log_entry = {
                'timestamp': ts,
                'response_time': response_time,
                'endpoint': np.random.choice(['/api/users', '/api/orders', '/api/products', '/api/auth']),
                'status_code': np.random.choice([200, 404, 500], p=[0.9, 0.05, 0.05]),
                'user_id': f"user_{np.random.randint(1, 1000)}",
                'request_size': np.random.randint(100, 5000),
                'response_size': np.random.randint(500, 50000)
            }
            
            data.append(log_entry)
        
        df = pd.DataFrame(data)
        return df
    
    def generate_database_logs(self, days: int = 7) -> pd.DataFrame:
        """Generate database performance logs"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        timestamps = pd.date_range(start=start_time, end=end_time, freq='10T')
        
        data = []
        for ts in timestamps:
            # Database query patterns
            query_time = np.random.exponential(100)  # Exponential distribution for query times
            
            # Add periodic spikes (every 4 hours for batch jobs)
            if ts.hour % 4 == 0 and ts.minute < 30:
                query_time *= np.random.uniform(3, 8)
            
            data.append({
                'timestamp': ts,
                'query_time': query_time,
                'query_type': np.random.choice(['SELECT', 'INSERT', 'UPDATE', 'DELETE']),
                'table_name': np.random.choice(['users', 'orders', 'products', 'logs']),
                'rows_affected': np.random.randint(1, 10000),
                'cpu_usage': min(100, np.random.normal(30, 15)),
                'memory_usage': min(100, np.random.normal(45, 20))
            })
        
        return pd.DataFrame(data)
    
    def generate_error_logs(self, days: int = 7) -> pd.DataFrame:
        """Generate error log patterns"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        timestamps = pd.date_range(start=start_time, end=end_time, freq='15T')
        
        data = []
        for ts in timestamps:
            # Error count with patterns
            base_errors = np.random.poisson(2)  # Base error rate
            
            # Higher errors during deployment times (every Tuesday 2 PM - example pattern)
            if ts.weekday() == 1 and 14 <= ts.hour <= 16:  # Tuesday 2-4 PM
                base_errors *= np.random.randint(5, 15)
            
            data.append({
                'timestamp': ts,
                'error_count': base_errors,
                'error_type': np.random.choice(['ConnectionError', 'TimeoutError', 'ValidationError', 'AuthError']),
                'severity': np.random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], p=[0.4, 0.3, 0.2, 0.1]),
                'service': np.random.choice(['web', 'api', 'database', 'cache', 'auth'])
            })
        
        return pd.DataFrame(data)
    
    def save_training_data(self):
        """Generate and save training data"""
        print("📊 Generating training data...")
        
        # Generate different types of logs
        web_logs = self.generate_web_server_logs(days=14)  # 2 weeks of data
        db_logs = self.generate_database_logs(days=14)  
        error_logs = self.generate_error_logs(days=14)
        
        # Save to files
        os.makedirs('data', exist_ok=True)
        web_logs.to_csv('data/web_server_logs.csv', index=False)
        db_logs.to_csv('data/database_logs.csv', index=False)
        error_logs.to_csv('data/error_logs.csv', index=False)
        
        # Also save to Redis for real-time access
        try:
            for _, row in web_logs.iterrows():
                key = f"web_log_{row['timestamp'].strftime('%Y%m%d_%H%M%S')}"
                self.redis_client.setex(key, 86400, json.dumps(row.to_dict(), default=str))
        except Exception as e:
            print(f"⚠️  Redis save failed: {e}")
        
        print(f"✅ Generated {len(web_logs)} web server logs")
        print(f"✅ Generated {len(db_logs)} database logs") 
        print(f"✅ Generated {len(error_logs)} error logs")
        
        return {
            'web_logs': len(web_logs),
            'db_logs': len(db_logs),
            'error_logs': len(error_logs)
        }

if __name__ == "__main__":
    generator = LogDataGenerator()
    generator.save_training_data()
