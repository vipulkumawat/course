"""
Metrics Collector for Capacity Planning
Collects historical metrics from monitoring systems
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yaml
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and aggregates historical metrics for capacity planning"""
    
    def __init__(self, config_path: str = 'config/planning_config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.historical_days = self.config['data_collection']['historical_days']
        self.aggregation_interval = self.config['data_collection']['aggregation_interval_minutes']
    
    def generate_synthetic_data(self, days: int = 90) -> pd.DataFrame:
        """
        Generate synthetic historical log volume data for demonstration
        Simulates realistic patterns: trend, seasonality, noise
        """
        logger.info(f"Generating {days} days of synthetic historical data...")
        
        # Create hourly timestamps
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        # Use periods instead of end to get exact number of hours
        timestamps = pd.date_range(start=start_date, periods=days*24, freq='1h')
        
        # Base trend: 10% monthly growth
        base_volume = 10000  # logs per second
        days_elapsed = np.arange(len(timestamps)) / 24  # days
        trend = base_volume * (1 + 0.10 * days_elapsed / 30)  # 10% monthly growth
        
        # Weekly seasonality (Monday peak, weekend dip)
        day_of_week = timestamps.dayofweek
        weekly_factor = np.where(day_of_week < 5, 1.2, 0.7)  # Weekday vs weekend
        
        # Daily seasonality (business hours peak)
        hour_of_day = timestamps.hour
        daily_factor = 0.5 + 0.5 * np.sin((hour_of_day - 6) * np.pi / 12)  # Peak at 12pm
        daily_factor = np.maximum(daily_factor, 0.3)  # Minimum 30% of peak
        
        # Random noise
        noise = np.random.normal(1.0, 0.1, len(timestamps))
        
        # Combine components
        log_volume = trend * weekly_factor * daily_factor * noise
        log_volume = np.maximum(log_volume, base_volume * 0.3)  # Floor at 30% of base
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'logs_per_second': log_volume,
            'cpu_usage_percent': np.minimum(log_volume / 500 + np.random.normal(20, 5, len(timestamps)), 100),
            'memory_usage_percent': np.minimum(log_volume / 600 + np.random.normal(40, 8, len(timestamps)), 100),
            'disk_usage_gb': np.cumsum(log_volume * 0.001) + np.random.normal(0, 10, len(timestamps))
        })
        
        logger.info(f"✅ Generated {len(df)} hourly data points")
        logger.info(f"   Log volume range: {df['logs_per_second'].min():.0f} - {df['logs_per_second'].max():.0f} logs/sec")
        
        return df
    
    def collect_historical_data(self, days: int = 90) -> pd.DataFrame:
        """
        Collect historical metrics from monitoring system
        For demo, uses synthetic data. In production, would query InfluxDB/Prometheus
        """
        # In production, would connect to actual monitoring DB:
        # client = InfluxDBClient(url=..., token=...)
        # query = f'from(bucket: "metrics") |> range(start: -{days}d)'
        # data = client.query_api().query_data_frame(query)
        
        return self.generate_synthetic_data(days)
    
    def save_historical_data(self, df: pd.DataFrame, filepath: str = 'data/historical.csv'):
        """Save collected data to CSV for analysis"""
        df.to_csv(filepath, index=False)
        logger.info(f"✅ Saved historical data to {filepath}")
    
    def load_historical_data(self, filepath: str = 'data/historical.csv') -> pd.DataFrame:
        """Load previously collected historical data"""
        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """Generate summary statistics of collected data"""
        return {
            'total_points': len(df),
            'date_range': {
                'start': df['timestamp'].min().isoformat(),
                'end': df['timestamp'].max().isoformat(),
                'days': (df['timestamp'].max() - df['timestamp'].min()).days
            },
            'log_volume': {
                'min': float(df['logs_per_second'].min()),
                'max': float(df['logs_per_second'].max()),
                'mean': float(df['logs_per_second'].mean()),
                'current': float(df['logs_per_second'].iloc[-1])
            }
        }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect historical metrics')
    parser.add_argument('--days', type=int, default=90, help='Days of history to collect')
    parser.add_argument('--validate', action='store_true', help='Validate collected data')
    parser.add_argument('--output', type=str, default='data/historical.csv', help='Output filepath')
    
    args = parser.parse_args()
    
    collector = MetricsCollector()
    df = collector.collect_historical_data(args.days)
    collector.save_historical_data(df, args.output)
    
    if args.validate:
        summary = collector.get_data_summary(df)
        print(f"\n✅ Collected {summary['total_points']} hourly data points ({summary['date_range']['days']} days)")
        print(f"   Log volume: {summary['log_volume']['min']:.0f} - {summary['log_volume']['max']:.0f} logs/sec")
