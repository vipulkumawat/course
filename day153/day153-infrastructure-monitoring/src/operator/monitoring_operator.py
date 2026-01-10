"""Kubernetes operator with monitoring integration"""
import time
import logging
from kubernetes import client, config, watch
from prometheus_client import Gauge
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Operator metrics
operator_reconciliations = Gauge('operator_reconciliations_total', 'Total reconciliations')
operator_scaling_events = Gauge('operator_scaling_events_total', 'Total scaling events')
cluster_pod_count = Gauge('cluster_log_processor_pods', 'Number of log processor pods')

class MonitoringAwareOperator:
    """K8s operator that uses monitoring data for intelligent decisions"""
    
    def __init__(self, prometheus_url='http://localhost:9090'):
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        self.prometheus_url = prometheus_url
        self.namespace = 'default'
        
    def query_prometheus(self, query):
        """Query Prometheus for metrics"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': query},
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                if result['data']['result']:
                    return float(result['data']['result'][0]['value'][1])
            return None
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return None
    
    def get_combined_metrics(self):
        """Get combined infrastructure and application metrics"""
        metrics = {}
        
        # Infrastructure metrics
        cpu_query = 'avg(rate(node_cpu_seconds_total{mode!="idle"}[1m])) * 100'
        metrics['cpu_percent'] = self.query_prometheus(cpu_query) or 0
        
        # Application metrics
        metrics['log_rate'] = self.query_prometheus('log_ingestion_rate') or 0
        metrics['queue_depth'] = self.query_prometheus('log_queue_depth') or 0
        
        # Latency p95
        latency_query = 'histogram_quantile(0.95, rate(log_processing_latency_seconds_bucket[5m]))'
        metrics['latency_p95'] = self.query_prometheus(latency_query) or 0
        
        return metrics
    
    def should_scale_up(self, metrics):
        """Determine if we should scale up based on combined metrics"""
        cpu_high = metrics['cpu_percent'] > 75
        queue_backing_up = metrics['queue_depth'] > 500
        latency_high = metrics['latency_p95'] > 0.5
        
        # Scale if any critical condition or two moderate conditions
        if cpu_high and queue_backing_up:
            return True, "High CPU and queue backup"
        if cpu_high and latency_high:
            return True, "High CPU and latency"
        if queue_backing_up and latency_high:
            return True, "Queue backup and high latency"
            
        return False, ""
    
    def should_scale_down(self, metrics):
        """Determine if we can scale down"""
        cpu_low = metrics['cpu_percent'] < 30
        queue_empty = metrics['queue_depth'] < 50
        latency_low = metrics['latency_p95'] < 0.1
        
        return cpu_low and queue_empty and latency_low, "Low resource usage"
    
    def scale_deployment(self, replicas, reason):
        """Scale the log processor deployment"""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name='log-processor',
                namespace=self.namespace
            )
            
            current_replicas = deployment.spec.replicas
            if current_replicas == replicas:
                return
            
            deployment.spec.replicas = replicas
            self.apps_v1.patch_namespaced_deployment(
                name='log-processor',
                namespace=self.namespace,
                body=deployment
            )
            
            operator_scaling_events.inc()
            cluster_pod_count.set(replicas)
            logger.info(f"Scaled from {current_replicas} to {replicas} replicas. Reason: {reason}")
            
        except Exception as e:
            logger.error(f"Error scaling deployment: {e}")
    
    def reconcile(self):
        """Main reconciliation loop"""
        logger.info("Starting monitoring-aware operator reconciliation loop")
        
        while True:
            try:
                operator_reconciliations.inc()
                
                # Get combined metrics
                metrics = self.get_combined_metrics()
                logger.info(f"Metrics: CPU={metrics['cpu_percent']:.1f}%, "
                          f"Queue={metrics['queue_depth']:.0f}, "
                          f"Latency={metrics['latency_p95']*1000:.1f}ms")
                
                # Make scaling decisions
                scale_up, up_reason = self.should_scale_up(metrics)
                scale_down, down_reason = self.should_scale_down(metrics)
                
                try:
                    deployment = self.apps_v1.read_namespaced_deployment(
                        name='log-processor',
                        namespace=self.namespace
                    )
                    current_replicas = deployment.spec.replicas
                    
                    if scale_up and current_replicas < 10:
                        self.scale_deployment(current_replicas + 1, up_reason)
                    elif scale_down and current_replicas > 1:
                        self.scale_deployment(current_replicas - 1, down_reason)
                        
                except client.exceptions.ApiException:
                    logger.info("log-processor deployment not found, skipping scaling")
                
                time.sleep(30)  # Reconcile every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("Shutting down operator")
                break
            except Exception as e:
                logger.error(f"Error in reconciliation loop: {e}")
                time.sleep(30)

if __name__ == '__main__':
    operator = MonitoringAwareOperator()
    operator.reconcile()
