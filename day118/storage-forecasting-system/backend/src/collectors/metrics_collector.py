import asyncio
import psutil
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List
import random

class StorageMetricsCollector:
    def __init__(self, node_id: str = "node-001", tenant_id: str = "default"):
        self.node_id = node_id
        self.tenant_id = tenant_id
        self.historical_data = []
        
    async def collect_current_metrics(self) -> Dict:
        """Collect current storage metrics"""
        disk_usage = psutil.disk_usage('/')
        
        # Simulate realistic log storage growth
        base_usage = disk_usage.used
        
        # Add some variability for realistic simulation
        current_time = datetime.now()
        hour_factor = 1.0 + 0.3 * (current_time.hour / 24)  # Higher usage during day
        day_factor = 1.0 + 0.1 * (current_time.weekday() / 7)  # Higher during weekdays
        random_factor = 1.0 + random.uniform(-0.05, 0.05)  # ±5% random variation
        
        simulated_usage = base_usage * hour_factor * day_factor * random_factor
        
        return {
            'timestamp': current_time,
            'node_id': self.node_id,
            'tenant_id': self.tenant_id,
            'storage_type': 'primary',
            'used_bytes': simulated_usage,
            'total_bytes': disk_usage.total,
            'utilization_percent': (simulated_usage / disk_usage.total) * 100,
            'metadata': {
                'disk_path': '/',
                'filesystem': 'ext4',
                'mount_point': '/'
            }
        }
    
    def generate_historical_data(self, days: int = 90) -> List[Dict]:
        """Generate historical data for simulation"""
        historical_data = []
        base_time = datetime.now()
        
        # Start with a base storage usage
        base_usage_gb = 100  # 100GB starting point
        
        for day in range(-days, 0):
            current_date = base_time + timedelta(days=day)
            
            # Simulate growth trend
            growth_rate = 0.02  # 2% growth per day
            trend_usage = base_usage_gb * (1 + growth_rate) ** abs(day)
            
            # Add daily patterns
            for hour in range(0, 24, 4):  # Every 4 hours
                timestamp = current_date.replace(hour=hour, minute=0, second=0)
                
                # Hour-based variations
                hour_multiplier = 1.0 + 0.2 * (hour / 24)
                
                # Day of week variations (higher on weekdays)
                weekday_multiplier = 1.2 if timestamp.weekday() < 5 else 0.8
                
                # Random variations
                random_multiplier = 1.0 + random.uniform(-0.1, 0.1)
                
                final_usage = trend_usage * hour_multiplier * weekday_multiplier * random_multiplier
                
                historical_data.append({
                    'timestamp': timestamp,
                    'node_id': self.node_id,
                    'tenant_id': self.tenant_id,
                    'storage_type': 'primary',
                    'used_bytes': final_usage * 1024**3,  # Convert GB to bytes
                    'total_bytes': 1000 * 1024**3,  # 1TB total
                    'utilization_percent': (final_usage / 1000) * 100,
                    'metadata': {'generated': True}
                })
        
        return historical_data
    
    async def start_collection(self, interval_seconds: int = 300):
        """Start continuous metrics collection"""
        print(f"🔍 Starting metrics collection for {self.node_id}")
        
        while True:
            try:
                metrics = await self.collect_current_metrics()
                self.historical_data.append(metrics)
                print(f"📊 Collected metrics: {metrics['used_bytes'] / 1024**3:.2f} GB used")
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                print(f"❌ Error collecting metrics: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute
