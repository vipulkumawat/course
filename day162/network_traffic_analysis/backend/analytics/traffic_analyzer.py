from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List
import random

class TrafficAnalyzer:
    """Analyze network traffic patterns and compute metrics"""
    
    def __init__(self, window_size=300):  # 5-minute window
        self.window_size = window_size
        self.connections = deque(maxlen=10000)
        self.metrics_history = deque(maxlen=100)
        self.baselines = {}
        
    def add_connection(self, connection: Dict):
        """Add a connection to the analysis window"""
        connection["timestamp"] = datetime.now()
        self.connections.append(connection)
    
    def get_current_metrics(self) -> Dict:
        """Calculate current traffic metrics"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_size)
        
        # Filter to current window
        recent = [c for c in self.connections if c.get("timestamp", now) > window_start]
        
        # Calculate metrics
        total_connections = len(recent)
        unique_sources = len(set(c.get("source_ip") for c in recent if c.get("source_ip")))
        unique_dests = len(set(c.get("dest_ip") for c in recent if c.get("dest_ip")))
        total_bytes = sum(c.get("bytes", 0) for c in recent)
        
        # Protocol distribution
        protocols = defaultdict(int)
        for conn in recent:
            proto = conn.get("protocol", "UNKNOWN")
            protocols[proto] += 1
        
        # Port distribution
        ports = defaultdict(int)
        for conn in recent:
            port = conn.get("dest_port")
            if port:
                ports[port] += 1
        
        # Top talkers
        src_bytes = defaultdict(int)
        for conn in recent:
            src = conn.get("source_ip")
            if src:
                src_bytes[src] += conn.get("bytes", 0)
        
        top_talkers = sorted(src_bytes.items(), key=lambda x: x[1], reverse=True)[:10]
        
        metrics = {
            "timestamp": now.isoformat(),
            "total_connections": total_connections,
            "unique_sources": unique_sources,
            "unique_destinations": unique_dests,
            "total_bytes": total_bytes,
            "connections_per_second": total_connections / self.window_size if self.window_size > 0 else 0,
            "bytes_per_second": total_bytes / self.window_size if self.window_size > 0 else 0,
            "protocols": dict(protocols),
            "top_ports": dict(sorted(ports.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_talkers": [{"ip": ip, "bytes": bytes} for ip, bytes in top_talkers],
            "connections": recent[-100:],  # Last 100 for pattern detection
            "auth_attempts": self._generate_auth_attempts(),
            "data_transfers": self._generate_data_transfers(recent),
            "dns_queries": self._generate_dns_queries()
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def _generate_auth_attempts(self) -> List[Dict]:
        """Generate authentication attempts for demo"""
        attempts = []
        # Simulate normal and failed auth attempts
        for _ in range(random.randint(5, 15)):
            attempts.append({
                "source_ip": f"192.168.1.{random.randint(1, 254)}",
                "success": random.random() > 0.1,  # 90% success rate
                "timestamp": datetime.now().isoformat()
            })
        return attempts
    
    def _generate_data_transfers(self, connections: List[Dict]) -> List[Dict]:
        """Extract data transfer information"""
        transfers = []
        for conn in connections:
            if conn.get("bytes", 0) > 1000:  # Only significant transfers
                transfers.append({
                    "source_ip": conn.get("source_ip"),
                    "dest_ip": conn.get("dest_ip"),
                    "bytes": conn.get("bytes"),
                    "direction": "outbound" if conn.get("source_ip", "").startswith("192.168") else "inbound",
                    "timestamp": conn.get("timestamp", datetime.now()).isoformat()
                })
        return transfers
    
    def _generate_dns_queries(self) -> List[Dict]:
        """Generate DNS queries for demo"""
        queries = []
        normal_domains = ["google.com", "facebook.com", "amazon.com", "github.com"]
        
        # Add normal queries
        for _ in range(random.randint(10, 20)):
            queries.append({
                "source_ip": f"192.168.1.{random.randint(1, 254)}",
                "query_domain": random.choice(normal_domains),
                "timestamp": datetime.now().isoformat()
            })
        
        # Occasionally add suspicious query
        if random.random() < 0.1:
            suspicious_domain = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=60)) + ".evil.com"
            queries.append({
                "source_ip": f"192.168.1.{random.randint(1, 254)}",
                "query_domain": suspicious_domain,
                "timestamp": datetime.now().isoformat()
            })
        
        return queries
    
    def calculate_baseline(self):
        """Calculate baseline metrics from historical data"""
        if len(self.metrics_history) < 10:
            return {}
        
        # Calculate averages
        total_conns = [m["total_connections"] for m in self.metrics_history]
        total_bytes_list = [m["total_bytes"] for m in self.metrics_history]
        
        import numpy as np
        
        self.baselines = {
            "connections_mean": np.mean(total_conns),
            "connections_std": np.std(total_conns),
            "bytes_mean": np.mean(total_bytes_list),
            "bytes_std": np.std(total_bytes_list)
        }
        
        return self.baselines
