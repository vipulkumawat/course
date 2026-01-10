"""Correlation engine for infrastructure and log metrics"""
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CorrelationEngine:
    """Correlates infrastructure metrics with log patterns"""
    
    def __init__(self, prometheus_url='http://localhost:9090'):
        self.prometheus_url = prometheus_url
        
    def query_range(self, query, start, end, step='15s'):
        """Query Prometheus for time range"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query_range",
                params={
                    'query': query,
                    'start': start.timestamp(),
                    'end': end.timestamp(),
                    'step': step
                },
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                if result['data']['result']:
                    values = result['data']['result'][0]['values']
                    return pd.DataFrame(values, columns=['timestamp', 'value'])
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return pd.DataFrame()
    
    def calculate_correlation(self, metric1_df, metric2_df):
        """Calculate correlation between two metrics"""
        if metric1_df.empty or metric2_df.empty:
            return 0.0
        
        # Align timestamps
        merged = pd.merge(metric1_df, metric2_df, on='timestamp', suffixes=('_1', '_2'))
        if len(merged) < 2:
            return 0.0
        
        merged['value_1'] = pd.to_numeric(merged['value_1'], errors='coerce')
        merged['value_2'] = pd.to_numeric(merged['value_2'], errors='coerce')
        
        correlation = merged['value_1'].corr(merged['value_2'])
        return correlation if not pd.isna(correlation) else 0.0
    
    def analyze_correlations(self, window_minutes=60):
        """Analyze correlations over time window"""
        end = datetime.now()
        start = end - timedelta(minutes=window_minutes)
        
        logger.info(f"Analyzing correlations from {start} to {end}")
        
        # Query metrics
        cpu_df = self.query_range('avg(rate(node_cpu_seconds_total{mode!="idle"}[1m])) * 100', start, end)
        latency_df = self.query_range('histogram_quantile(0.95, rate(log_processing_latency_seconds_bucket[5m]))', start, end)
        queue_df = self.query_range('log_queue_depth', start, end)
        rate_df = self.query_range('log_ingestion_rate', start, end)
        
        # Calculate correlations
        correlations = {
            'cpu_vs_latency': self.calculate_correlation(cpu_df, latency_df),
            'cpu_vs_queue': self.calculate_correlation(cpu_df, queue_df),
            'queue_vs_latency': self.calculate_correlation(queue_df, latency_df),
            'rate_vs_cpu': self.calculate_correlation(rate_df, cpu_df)
        }
        
        logger.info("Correlation Analysis Results:")
        for pair, corr in correlations.items():
            logger.info(f"  {pair}: {corr:.3f}")
        
        # Identify strong correlations
        strong_correlations = {k: v for k, v in correlations.items() if abs(v) > 0.7}
        if strong_correlations:
            logger.info(f"Strong correlations found: {strong_correlations}")
        
        return correlations
    
    def detect_anomalies(self, window_minutes=30):
        """Detect anomalies using combined metrics"""
        end = datetime.now()
        start = end - timedelta(minutes=window_minutes)
        
        cpu_df = self.query_range('avg(rate(node_cpu_seconds_total{mode!="idle"}[1m])) * 100', start, end)
        latency_df = self.query_range('histogram_quantile(0.95, rate(log_processing_latency_seconds_bucket[5m]))', start, end)
        
        anomalies = []
        
        # Check for unusual CPU patterns
        if not cpu_df.empty:
            cpu_df['value'] = pd.to_numeric(cpu_df['value'], errors='coerce')
            cpu_mean = cpu_df['value'].mean()
            cpu_std = cpu_df['value'].std()
            
            recent_cpu = cpu_df['value'].iloc[-5:].mean() if len(cpu_df) >= 5 else 0
            
            if recent_cpu > cpu_mean + 2 * cpu_std:
                anomalies.append({
                    'type': 'cpu_spike',
                    'severity': 'high',
                    'value': recent_cpu,
                    'message': f'CPU usage {recent_cpu:.1f}% is unusually high'
                })
        
        # Check for unusual latency
        if not latency_df.empty:
            latency_df['value'] = pd.to_numeric(latency_df['value'], errors='coerce')
            latency_mean = latency_df['value'].mean()
            latency_std = latency_df['value'].std()
            
            recent_latency = latency_df['value'].iloc[-5:].mean() if len(latency_df) >= 5 else 0
            
            if recent_latency > latency_mean + 2 * latency_std:
                anomalies.append({
                    'type': 'latency_spike',
                    'severity': 'high',
                    'value': recent_latency,
                    'message': f'Processing latency {recent_latency*1000:.1f}ms is unusually high'
                })
        
        return anomalies

def run_correlation_analysis():
    """Run continuous correlation analysis"""
    engine = CorrelationEngine()
    
    logger.info("Starting correlation analysis engine")
    
    while True:
        try:
            # Analyze correlations
            correlations = engine.analyze_correlations(window_minutes=30)
            
            # Detect anomalies
            anomalies = engine.detect_anomalies(window_minutes=15)
            
            if anomalies:
                logger.warning(f"Detected {len(anomalies)} anomalies:")
                for anomaly in anomalies:
                    logger.warning(f"  {anomaly['type']}: {anomaly['message']}")
            
            time.sleep(60)  # Analyze every minute
            
        except KeyboardInterrupt:
            logger.info("Shutting down correlation engine")
            break
        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}")
            time.sleep(60)

if __name__ == '__main__':
    run_correlation_analysis()
