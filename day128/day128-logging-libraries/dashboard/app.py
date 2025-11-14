import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'day128-multi-language-logging'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state for demonstration
received_logs: List[Dict[str, Any]] = []
language_stats: Dict[str, Dict[str, int]] = {
    'python': {'logs_sent': 0, 'logs_failed': 0, 'batches_sent': 0},
    'java': {'logs_sent': 0, 'logs_failed': 0, 'batches_sent': 0},
    'nodejs': {'logs_sent': 0, 'logs_failed': 0, 'batches_sent': 0},
    'dotnet': {'logs_sent': 0, 'logs_failed': 0, 'batches_sent': 0}
}

log_levels_count = {
    'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0
}

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/logs', methods=['POST'])
def receive_logs():
    """API endpoint to receive logs from client libraries"""
    try:
        logs_data = request.get_json()
        
        if isinstance(logs_data, list):
            # Batch of logs
            for log_entry in logs_data:
                process_log_entry(log_entry)
            
            # Update stats
            language = determine_language_from_request(request)
            language_stats[language]['logs_sent'] += len(logs_data)
            language_stats[language]['batches_sent'] += 1
            
            # Emit real-time updates
            socketio.emit('logs_received', {
                'count': len(logs_data),
                'language': language,
                'timestamp': datetime.now().isoformat()
            })
            
        else:
            # Single log entry
            process_log_entry(logs_data)
            language = determine_language_from_request(request)
            language_stats[language]['logs_sent'] += 1
        
        return jsonify({'status': 'success', 'received': len(logs_data) if isinstance(logs_data, list) else 1})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

def process_log_entry(log_entry: Dict[str, Any]):
    """Process individual log entry"""
    # Add to received logs (keep last 1000)
    received_logs.append({
        **log_entry,
        'received_at': datetime.now().isoformat()
    })
    
    if len(received_logs) > 1000:
        received_logs.pop(0)
    
    # Update level counts
    level = log_entry.get('level', 'INFO')
    if level in log_levels_count:
        log_levels_count[level] += 1
    
    # Emit to dashboard
    socketio.emit('new_log', log_entry)

def determine_language_from_request(request) -> str:
    """Determine which language sent the request based on headers or content"""
    user_agent = request.headers.get('User-Agent', '').lower()
    
    if 'python' in user_agent or 'aiohttp' in user_agent:
        return 'python'
    elif 'java' in user_agent or 'apache' in user_agent:
        return 'java'
    elif 'node' in user_agent or 'axios' in user_agent:
        return 'nodejs'
    elif 'dotnet' in user_agent or '.net' in user_agent:
        return 'dotnet'
    else:
        # Default fallback - could be improved with more sophisticated detection
        return random.choice(['python', 'java', 'nodejs', 'dotnet'])

@app.route('/api/stats')
def get_stats():
    """Get current statistics"""
    total_logs = sum(lang['logs_sent'] for lang in language_stats.values())
    total_batches = sum(lang['batches_sent'] for lang in language_stats.values())
    
    return jsonify({
        'total_logs': total_logs,
        'total_batches': total_batches,
        'language_stats': language_stats,
        'log_levels': log_levels_count,
        'recent_logs_count': len(received_logs),
        'uptime': time.time() - start_time
    })

@app.route('/api/recent-logs')
def get_recent_logs():
    """Get recent log entries"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify(received_logs[-limit:])

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    emit('connected', {'message': 'Connected to logging dashboard'})
    emit('stats_update', {
        'language_stats': language_stats,
        'log_levels': log_levels_count
    })

# Background task to simulate some demo logs
def generate_demo_logs():
    """Generate demo logs for demonstration purposes"""
    demo_messages = [
        "User authentication successful",
        "Database query executed",
        "Cache hit for user profile",
        "API rate limit warning",
        "Background job completed",
        "Memory usage threshold exceeded",
        "File upload processing started",
        "Payment processing completed"
    ]
    
    while True:
        time.sleep(random.uniform(2, 8))
        
        # Generate a demo log
        level = random.choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'])
        message = random.choice(demo_messages)
        language = random.choice(['python', 'java', 'nodejs', 'dotnet'])
        
        demo_log = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'service': 'demo-service',
            'component': 'demo-component',
            'metadata': {
                'demo': True,
                'source_language': language,
                'random_id': random.randint(1000, 9999)
            },
            'request_id': f'demo-{random.randint(10000, 99999)}'
        }
        
        process_log_entry(demo_log)
        language_stats[language]['logs_sent'] += 1

if __name__ == '__main__':
    start_time = time.time()
    
    # Start demo log generator in background
    demo_thread = threading.Thread(target=generate_demo_logs, daemon=True)
    demo_thread.start()
    
    print("🚀 Multi-Language Logging Dashboard starting...")
    print("📊 Dashboard available at: http://127.0.0.1:5000")
    print("🔌 API endpoint: http://127.0.0.1:5000/api/logs")
    
    # Use 0.0.0.0 to listen on all interfaces (for WSL2 Windows host access)
    # But recommend using 127.0.0.1 in browser to avoid IPv6 issues
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
