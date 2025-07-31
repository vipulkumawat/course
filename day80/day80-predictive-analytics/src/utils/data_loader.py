import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import redis
import json
import sys
# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.config import config

class DataLoader:
    """Load training data for model training"""
    
    def __init__(self):
        self.redis_client = redis.from_url(config.redis_url)
    
    def load_training_data(self, metric: str = 'response_time') -> pd.DataFrame:
        """Load training data for specified metric"""
        try:
            # Try to load from CSV files first
            if metric == 'response_time':
                file_path = 'data/web_server_logs.csv'
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    return df[['timestamp', metric]].dropna()
            
            elif metric == 'query_time':
                file_path = 'data/database_logs.csv'
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    return df[['timestamp', metric]].dropna()
            
            elif metric == 'error_count':
                file_path = 'data/error_logs.csv'
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    return df[['timestamp', metric]].dropna()
            
            # Fallback: generate sample data if files don't exist
            print(f"⚠️  No data file found for {metric}, generating sample data...")
            return self._generate_sample_data(metric)
            
        except Exception as e:
            print(f"❌ Error loading training data: {e}")
            return self._generate_sample_data(metric)
    
    def _generate_sample_data(self, metric: str = 'response_time') -> pd.DataFrame:
        """Generate sample data for training"""
        # Generate 7 days of hourly data
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        timestamps = pd.date_range(start=start_time, end=end_time, freq='5T')
        
        if metric == 'response_time':
            values = 50 + 20 * np.sin(np.arange(len(timestamps)) * 2 * np.pi / 288) + np.random.normal(0, 10, len(timestamps))
            values = np.maximum(values, 10)  # Minimum 10ms
        elif metric == 'query_time':
            values = 100 + 50 * np.sin(np.arange(len(timestamps)) * 2 * np.pi / 144) + np.random.exponential(30, len(timestamps))
        elif metric == 'error_count':
            values = np.random.poisson(3, len(timestamps))
        else:
            values = np.random.normal(50, 15, len(timestamps))
        
        return pd.DataFrame({
            'timestamp': timestamps,
            metric: values
        })
