"""
Log Collector - Ingests logs and sends to RabbitMQ
"""
import os
import time
import random
import signal
import sys

class LogCollector:
    def __init__(self):
        self.rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.running = True
        self.logs_collected = 0
        
    def collect_logs(self):
        log_messages = [
            {'level': 'INFO', 'message': 'Application started successfully'},
            {'level': 'ERROR', 'message': 'Database connection timeout'},
            {'level': 'WARNING', 'message': 'High memory usage detected'},
            {'level': 'DEBUG', 'message': 'Processing request ID: 12345'}
        ]
        
        while self.running:
            log = random.choice(log_messages)
            log['timestamp'] = time.time()
            log['collector_id'] = os.getenv('HOSTNAME', 'collector-0')
            
            self.logs_collected += 1
            print(f"[{log['level']}] {log['message']} (Total: {self.logs_collected})")
            
            time.sleep(5)  # Collect every 5 seconds

collector = LogCollector()

def signal_handler(sig, frame):
    print("\nShutting down log collector")
    collector.running = False
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"Log collector starting (RabbitMQ: {collector.rabbitmq_host})")
    collector.collect_logs()
