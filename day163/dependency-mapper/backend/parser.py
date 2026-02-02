"""
Log parser for extracting service dependencies
Supports multiple log formats: HTTP, RPC, Database
"""
import re
from datetime import datetime
from typing import Dict, Optional, Tuple

class DependencyParser:
    def __init__(self):
        self.patterns = {
            'http': r'(\w+)\s+called\s+(\w+)\s+(GET|POST|PUT|DELETE)\s+(\S+)\s+(\d+)ms',
            'rpc': r'(\w+)\s*->\s*(\w+)\.(\w+)\(\)\s+(\d+)ms',
            'db': r'(\w+)\s*->\s*(PostgreSQL|MySQL|MongoDB)\s+(SELECT|INSERT|UPDATE|DELETE)\s+(\w+)\s+(\d+)ms',
            'generic': r'(\w+)\s*->\s*(\w+)\s+(\d+)ms'
        }
    
    def parse_log_line(self, line: str) -> Optional[Dict]:
        """Parse a single log line and extract dependency information"""
        timestamp_match = re.search(r'\[([\d\-: ]+)\]', line)
        timestamp = datetime.fromisoformat(timestamp_match.group(1)) if timestamp_match else datetime.now()
        
        # Try HTTP pattern
        match = re.search(self.patterns['http'], line)
        if match:
            return {
                'caller': match.group(1),
                'callee': match.group(2),
                'type': 'http',
                'method': match.group(3),
                'endpoint': match.group(4),
                'latency': int(match.group(5)),
                'timestamp': timestamp
            }
        
        # Try RPC pattern
        match = re.search(self.patterns['rpc'], line)
        if match:
            return {
                'caller': match.group(1),
                'callee': match.group(2),
                'type': 'rpc',
                'method': match.group(3),
                'latency': int(match.group(4)),
                'timestamp': timestamp
            }
        
        # Try database pattern
        match = re.search(self.patterns['db'], line)
        if match:
            return {
                'caller': match.group(1),
                'callee': match.group(2),
                'type': 'database',
                'operation': match.group(3),
                'table': match.group(4),
                'latency': int(match.group(5)),
                'timestamp': timestamp
            }
        
        # Try generic pattern
        match = re.search(self.patterns['generic'], line)
        if match:
            return {
                'caller': match.group(1),
                'callee': match.group(2),
                'type': 'generic',
                'latency': int(match.group(3)),
                'timestamp': timestamp
            }
        
        return None

    def parse_log_file(self, filepath: str):
        """Parse entire log file and yield dependencies"""
        with open(filepath, 'r') as f:
            for line in f:
                dep = self.parse_log_line(line.strip())
                if dep:
                    yield dep
