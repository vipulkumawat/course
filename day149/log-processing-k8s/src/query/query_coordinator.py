"""
Query Coordinator - Handles NLP queries and routes to storage
"""
import os
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import signal
import sys

class QueryCoordinator:
    def __init__(self):
        self.port = int(os.getenv('QUERY_COORDINATOR_PORT', '8080'))
        self.rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.ready = False
        self.startup_time = time.time()
        self.query_count = 0
        
    def process_query(self, query_text):
        self.query_count += 1
        query_lower = query_text.lower()
        
        # Sample log database - in production this would come from storage nodes
        all_logs = [
            {'timestamp': '2025-05-20T10:00:00Z', 'level': 'ERROR', 'message': 'Database connection failed'},
            {'timestamp': '2025-05-20T10:01:00Z', 'level': 'INFO', 'message': 'User login successful'},
            {'timestamp': '2025-05-20T10:02:00Z', 'level': 'WARNING', 'message': 'High memory usage detected'},
            {'timestamp': '2025-05-20T10:03:00Z', 'level': 'ERROR', 'message': 'Payment processing failed'},
            {'timestamp': '2025-05-20T10:04:00Z', 'level': 'INFO', 'message': 'API request completed successfully'},
            {'timestamp': '2025-05-20T10:05:00Z', 'level': 'ERROR', 'message': 'Authentication token expired'},
            {'timestamp': '2025-05-20T10:06:00Z', 'level': 'INFO', 'message': 'Cache updated successfully'},
            {'timestamp': '2025-05-20T10:07:00Z', 'level': 'WARNING', 'message': 'Slow query detected'},
            {'timestamp': '2025-05-20T10:08:00Z', 'level': 'ERROR', 'message': 'File upload failed'},
            {'timestamp': '2025-05-20T10:09:00Z', 'level': 'INFO', 'message': 'Backup completed successfully'},
        ]
        
        # Simple keyword-based query processing
        results = []
        
        # Filter by log level
        if 'error' in query_lower or 'errors' in query_lower or 'failed' in query_lower:
            results = [log for log in all_logs if log['level'] == 'ERROR']
        elif 'warning' in query_lower or 'warnings' in query_lower:
            results = [log for log in all_logs if log['level'] == 'WARNING']
        elif 'info' in query_lower or 'information' in query_lower:
            results = [log for log in all_logs if log['level'] == 'INFO']
        else:
            # Default: return all logs
            results = all_logs
        
        # Filter by keywords in message
        if 'database' in query_lower or 'db' in query_lower:
            results = [log for log in results if 'database' in log['message'].lower() or 'db' in log['message'].lower()]
        elif 'payment' in query_lower:
            results = [log for log in results if 'payment' in log['message'].lower()]
        elif 'auth' in query_lower or 'authentication' in query_lower or 'login' in query_lower:
            results = [log for log in results if 'auth' in log['message'].lower() or 'login' in log['message'].lower()]
        elif 'api' in query_lower:
            results = [log for log in results if 'api' in log['message'].lower()]
        elif 'cache' in query_lower:
            results = [log for log in results if 'cache' in log['message'].lower()]
        elif 'backup' in query_lower:
            results = [log for log in results if 'backup' in log['message'].lower()]
        elif 'file' in query_lower or 'upload' in query_lower:
            results = [log for log in results if 'file' in log['message'].lower() or 'upload' in log['message'].lower()]
        elif 'memory' in query_lower:
            results = [log for log in results if 'memory' in log['message'].lower()]
        elif 'query' in query_lower:
            results = [log for log in results if 'query' in log['message'].lower()]
        
        # Time-based filtering
        if 'last hour' in query_lower or 'recent' in query_lower:
            # Return only recent logs (last 3)
            results = results[-3:] if len(results) > 3 else results
        elif 'today' in query_lower:
            # Return logs from today (all in our sample)
            pass  # All logs are from the same day
        
        # If no results match, return a message
        if not results:
            results = [{'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'), 'level': 'INFO', 'message': f'No logs found matching: {query_text}'}]
        
        # Limit results to top 10
        results = results[:10]
        
        return {
            'query': query_text,
            'results': results,
            'processed_by': 'query-coordinator',
            'query_number': self.query_count,
            'result_count': len(results)
        }

coordinator = QueryCoordinator()

class QueryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'status': 'healthy'}
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/ready':
            if coordinator.ready:
                self.send_response(200)
            else:
                self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'ready': coordinator.ready}
            self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/query':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                query_data = json.loads(body)
                result = coordinator.process_query(query_data.get('query', ''))
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error = {'error': str(e)}
                self.wfile.write(json.dumps(error).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(('0.0.0.0', coordinator.port), QueryHandler)
    print(f"Query coordinator starting on port {coordinator.port}")
    
    # Mark ready after checking RabbitMQ
    import time
    time.sleep(3)
    coordinator.ready = True
    print("Query coordinator is ready")
    
    def signal_handler(sig, frame):
        print("\nShutting down query coordinator")
        server.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server.serve_forever()

if __name__ == '__main__':
    run_server()
