"""
Storage Node - Handles log storage and retrieval
"""
import os
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import signal
import sys

class StorageNode:
    def __init__(self):
        self.node_id = os.getenv('NODE_ID', 'storage-node-0')
        self.port = int(os.getenv('STORAGE_PORT', '9090'))
        self.data = {}
        self.ready = False
        self.startup_time = time.time()
        
    def store_log(self, log_id, log_data):
        self.data[log_id] = {
            'data': log_data,
            'timestamp': time.time(),
            'node': self.node_id
        }
        return True
        
    def get_log(self, log_id):
        return self.data.get(log_id)
        
    def get_stats(self):
        return {
            'node_id': self.node_id,
            'total_logs': len(self.data),
            'uptime': time.time() - self.startup_time,
            'status': 'ready' if self.ready else 'starting'
        }

storage = StorageNode()

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'status': 'healthy', 'node': storage.node_id}
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/ready':
            if storage.ready:
                self.send_response(200)
            else:
                self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'ready': storage.ready, 'node': storage.node_id}
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/stats':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(storage.get_stats()).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(('0.0.0.0', storage.port), HealthHandler)
    print(f"Storage node {storage.node_id} starting on port {storage.port}")
    
    # Mark ready after 5 seconds (simulating startup)
    def mark_ready():
        time.sleep(5)
        storage.ready = True
        print(f"Storage node {storage.node_id} is ready")
    
    Thread(target=mark_ready, daemon=True).start()
    
    def signal_handler(sig, frame):
        print(f"\nShutting down storage node {storage.node_id}")
        server.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server.serve_forever()

if __name__ == '__main__':
    run_server()
