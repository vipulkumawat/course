"""Web dashboard for CloudWatch collector."""
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from prometheus_client import generate_latest, REGISTRY
import logging
import threading
import time

logger = logging.getLogger(__name__)

app = Flask(__name__, 
           template_folder='../../web/templates',
           static_folder='../../web/static')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global stats
stats = {
    'logs_processed': 0,
    'logs_forwarded': 0,
    'logs_dropped': 0,
    'active_log_groups': 0,
    'buffer_size': 0
}

# Store collector reference for test data injection
_collector_instance = None


@app.route('/')
def index():
    """Dashboard home page."""
    response = app.make_response(render_template('dashboard.html'))
    # Prevent caching of the dashboard
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/api/stats')
def get_stats():
    """Get current statistics."""
    return jsonify(stats)


@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(REGISTRY)


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

@app.route('/api/test/inject', methods=['POST'])
def inject_test_data():
    """Inject test data into the pipeline for testing."""
    from flask import request
    from ..models.log_entry import CloudWatchLogEntry
    
    if _collector_instance is None:
        return jsonify({'error': 'Collector not available'}), 500
    
    try:
        # Get count from request or use default
        count = request.json.get('count', 100) if request.json else 100
        
        # Generate test log entries
        import random
        test_messages = [
            "ERROR: Database connection failed",
            "WARN: High memory usage detected",
            "INFO: Processing request",
            "ERROR: Exception in handler",
            "WARN: Retry attempt failed",
            "INFO: Successfully processed batch",
            "ERROR: Timeout waiting for response",
            "WARN: Deprecated API used",
        ]
        
        log_entries = []
        for i in range(count):
            entry = CloudWatchLogEntry(
                timestamp=int(time.time() * 1000) - random.randint(0, 3600000),
                message=random.choice(test_messages),
                log_group=f"/aws/test/log-group-{random.randint(1, 5)}",
                log_stream=f"stream-{random.randint(1, 10)}",
                region="us-east-1",
                account_id="test-account",
                service="test-service"
            )
            log_entries.append(entry)
        
        # Inject logs into pipeline
        _collector_instance.pipeline.add_logs(log_entries)
        
        return jsonify({
            'success': True,
            'injected': count,
            'message': f'Injected {count} test log entries'
        })
    
    except Exception as e:
        logger.error(f"Error injecting test data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def update_stats_loop(collector):
    """Background loop to update stats from collector."""
    import requests
    import os
    
    prometheus_port = int(os.getenv('PROMETHEUS_PORT', 8000))
    
    while True:
        try:
            # Query metrics endpoint
            try:
                response = requests.get(f'http://localhost:{prometheus_port}/metrics', timeout=1)
                if response.status_code == 200:
                    for line in response.text.split('\n'):
                        line = line.strip()
                        # Skip comments and empty lines
                        if not line or line.startswith('#'):
                            continue
                        
                        # Parse metric lines
                        if line.startswith('cloudwatch_logs_processed_total '):
                            parts = line.split()
                            if len(parts) >= 2:
                                stats['logs_processed'] = int(float(parts[1]))
                        elif line.startswith('cloudwatch_logs_forwarded_total '):
                            parts = line.split()
                            if len(parts) >= 2:
                                stats['logs_forwarded'] = int(float(parts[1]))
                        elif line.startswith('cloudwatch_logs_dropped_total '):
                            parts = line.split()
                            if len(parts) >= 2:
                                stats['logs_dropped'] = int(float(parts[1]))
                        elif line.startswith('cloudwatch_buffer_size '):
                            parts = line.split()
                            if len(parts) >= 2:
                                stats['buffer_size'] = int(float(parts[1]))
            except Exception as e:
                logger.debug(f"Could not fetch metrics from endpoint: {e}")
            
            # Emit to connected clients
            socketio.emit('stats_update', stats)
            
        except Exception as e:
            logger.error(f"Stats update error: {e}", exc_info=True)
        
        time.sleep(2)


def start_dashboard(collector, host='0.0.0.0', port=5000):
    """Start dashboard server."""
    global _collector_instance
    _collector_instance = collector
    
    # Start stats update thread
    stats_thread = threading.Thread(
        target=update_stats_loop,
        args=(collector,),
        daemon=True
    )
    stats_thread.start()
    
    # Start Flask with template auto-reload enabled
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
