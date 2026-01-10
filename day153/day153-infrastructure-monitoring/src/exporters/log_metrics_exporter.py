"""Custom Prometheus exporter for log processing metrics"""
import time
import random
from prometheus_client import start_http_server, Gauge, Counter, Histogram
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
import psutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define metrics
log_ingestion_rate = Gauge('log_ingestion_rate', 'Logs ingested per second')
log_processing_latency = Histogram('log_processing_latency_seconds', 
                                    'Log processing latency',
                                    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0))
log_errors_total = Counter('log_errors_total', 'Total log processing errors', ['error_type'])
queue_depth = Gauge('log_queue_depth', 'Current log queue depth')
partition_lag = Gauge('log_partition_lag', 'Consumer lag per partition', ['partition'])
cpu_usage_percent = Gauge('app_cpu_usage_percent', 'Application CPU usage')
memory_usage_mb = Gauge('app_memory_usage_mb', 'Application memory usage in MB')

class LogMetricsCollector:
    """Collects and exposes log processing metrics"""
    
    def __init__(self):
        self.base_ingestion_rate = 1000
        self.base_latency = 0.05
        self.queue_size = 0
        
    def collect_metrics(self):
        """Simulate metric collection from actual log processing"""
        # Simulate varying ingestion rate
        variation = random.uniform(0.8, 1.2)
        current_rate = self.base_ingestion_rate * variation
        log_ingestion_rate.set(current_rate)
        
        # Simulate processing latency correlated with CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_usage_percent.set(cpu_percent)
        
        # Latency increases with CPU usage
        latency_factor = 1 + (cpu_percent / 100)
        current_latency = self.base_latency * latency_factor
        log_processing_latency.observe(current_latency)
        
        # Memory metrics
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        memory_usage_mb.set(memory_mb)
        
        # Queue depth - grows when CPU is high
        if cpu_percent > 70:
            self.queue_size += random.randint(10, 50)
        else:
            self.queue_size = max(0, self.queue_size - random.randint(5, 20))
        queue_depth.set(self.queue_size)
        
        # Partition lag
        for partition in range(3):
            lag = random.randint(0, 100) if cpu_percent > 80 else random.randint(0, 10)
            partition_lag.labels(partition=f"partition-{partition}").set(lag)
        
        # Error simulation
        if random.random() < 0.01:  # 1% error rate
            error_type = random.choice(['parsing', 'timeout', 'validation'])
            log_errors_total.labels(error_type=error_type).inc()
        
        logger.info(f"Metrics: Rate={current_rate:.0f} logs/s, Latency={current_latency*1000:.1f}ms, "
                   f"CPU={cpu_percent:.1f}%, Queue={self.queue_size}")

def run_exporter(port=8000):
    """Run the metrics exporter"""
    logger.info(f"Starting log metrics exporter on port {port}")
    start_http_server(port)
    
    collector = LogMetricsCollector()
    
    logger.info("Collecting metrics every 5 seconds...")
    while True:
        try:
            collector.collect_metrics()
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Shutting down exporter")
            break
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

if __name__ == '__main__':
    run_exporter()
