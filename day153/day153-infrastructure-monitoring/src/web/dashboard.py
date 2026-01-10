"""Web dashboard for unified monitoring"""
from flask import Flask, render_template, jsonify
import requests
from datetime import datetime, timedelta
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROMETHEUS_URL = os.environ.get('PROMETHEUS_URL', 'http://localhost:9090')

def query_prometheus(query):
    """Query Prometheus"""
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={'query': query},
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            if result['data']['result']:
                return float(result['data']['result'][0]['value'][1])
        return 0
    except:
        return 0

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    """Get current metrics"""
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'infrastructure': {
            'cpu_percent': round(query_prometheus('avg(rate(node_cpu_seconds_total{mode!="idle"}[1m])) * 100'), 2),
            'memory_percent': round(query_prometheus('(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'), 2),
            'disk_usage_percent': round(query_prometheus('(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100'), 2)
        },
        'application': {
            'log_rate': round(query_prometheus('log_ingestion_rate'), 0),
            'latency_p95': round(query_prometheus('histogram_quantile(0.95, rate(log_processing_latency_seconds_bucket[5m]))') * 1000, 2),
            'queue_depth': round(query_prometheus('log_queue_depth'), 0),
            'error_rate': round(query_prometheus('rate(log_errors_total[5m])'), 2)
        },
        'cluster': {
            'pod_count': round(query_prometheus('cluster_log_processor_pods'), 0),
            'scaling_events': round(query_prometheus('operator_scaling_events_total'), 0)
        }
    }
    
    return jsonify(metrics)

@app.route('/api/correlations')
def get_correlations():
    """Get correlation data"""
    # This would call the correlation engine
    return jsonify({
        'cpu_vs_latency': 0.85,
        'cpu_vs_queue': 0.72,
        'queue_vs_latency': 0.68
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
