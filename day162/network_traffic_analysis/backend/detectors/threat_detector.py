from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
import math

class ThreatDetector:
    """Detect network security threats using pattern matching"""
    
    def __init__(self):
        self.connection_tracker = defaultdict(lambda: {
            "ports": set(),
            "connections": 0,
            "failed_auth": 0,
            "bytes_sent": 0,
            "last_seen": datetime.now()
        })
        self.dns_tracker = defaultdict(lambda: {
            "queries": [],
            "domains": set()
        })
        
    def detect_threats(self, metrics: Dict) -> List[Dict]:
        """Detect threats from traffic metrics"""
        threats = []
        
        # Port scan detection
        port_scan_threats = self._detect_port_scans(metrics.get("connections", []))
        threats.extend(port_scan_threats)
        
        # Brute force detection
        brute_force_threats = self._detect_brute_force(metrics.get("auth_attempts", []))
        threats.extend(brute_force_threats)
        
        # Data exfiltration detection
        exfil_threats = self._detect_exfiltration(metrics.get("data_transfers", []))
        threats.extend(exfil_threats)
        
        # DNS tunneling detection
        dns_threats = self._detect_dns_tunneling(metrics.get("dns_queries", []))
        threats.extend(dns_threats)
        
        return threats
    
    def _detect_port_scans(self, connections: List[Dict]) -> List[Dict]:
        """Detect port scanning activity"""
        threats = []
        port_tracker = defaultdict(set)
        
        # Track unique ports per source IP
        for conn in connections:
            src = conn.get("source_ip")
            port = conn.get("dest_port")
            if src and port:
                port_tracker[src].add(port)
        
        # Flag sources touching many ports
        for src_ip, ports in port_tracker.items():
            if len(ports) > 20:  # Threshold for port scan
                threat_score = min(100, 50 + len(ports))
                threats.append({
                    "type": "port_scan",
                    "source_ip": src_ip,
                    "threat_score": threat_score,
                    "details": f"Scanned {len(ports)} ports",
                    "severity": "critical" if threat_score > 80 else "high",
                    "timestamp": datetime.now().isoformat()
                })
        
        return threats
    
    def _detect_brute_force(self, auth_attempts: List[Dict]) -> List[Dict]:
        """Detect brute force authentication attempts"""
        threats = []
        failure_tracker = defaultdict(int)
        
        for attempt in auth_attempts:
            if not attempt.get("success"):
                src = attempt.get("source_ip")
                failure_tracker[src] += 1
        
        for src_ip, failures in failure_tracker.items():
            if failures > 10:  # Threshold for brute force
                threats.append({
                    "type": "brute_force",
                    "source_ip": src_ip,
                    "threat_score": min(100, 60 + failures * 2),
                    "details": f"{failures} failed authentication attempts",
                    "severity": "critical",
                    "timestamp": datetime.now().isoformat()
                })
        
        return threats
    
    def _detect_exfiltration(self, transfers: List[Dict]) -> List[Dict]:
        """Detect unusual data exfiltration"""
        threats = []
        upload_tracker = defaultdict(int)
        
        for transfer in transfers:
            if transfer.get("direction") == "outbound":
                src = transfer.get("source_ip")
                bytes_sent = transfer.get("bytes", 0)
                upload_tracker[src] += bytes_sent
        
        # Check for unusual upload volumes (>100MB)
        for src_ip, total_bytes in upload_tracker.items():
            mb_uploaded = total_bytes / (1024 * 1024)
            if mb_uploaded > 100:
                threats.append({
                    "type": "data_exfiltration",
                    "source_ip": src_ip,
                    "threat_score": min(100, 70 + int(mb_uploaded / 10)),
                    "details": f"Uploaded {mb_uploaded:.2f}MB",
                    "severity": "high",
                    "timestamp": datetime.now().isoformat()
                })
        
        return threats
    
    def _detect_dns_tunneling(self, dns_queries: List[Dict]) -> List[Dict]:
        """Detect DNS tunneling attempts"""
        threats = []
        
        for query in dns_queries:
            domain = query.get("query_domain", "")
            
            # Check domain length (tunneling uses long subdomains)
            if len(domain) > 50:
                entropy = self._calculate_entropy(domain)
                
                # High entropy + long domain = likely tunneling
                if entropy > 3.5:
                    threats.append({
                        "type": "dns_tunneling",
                        "source_ip": query.get("source_ip"),
                        "domain": domain,
                        "threat_score": 75,
                        "details": f"Suspicious DNS query: entropy={entropy:.2f}, length={len(domain)}",
                        "severity": "medium",
                        "timestamp": datetime.now().isoformat()
                    })
        
        return threats
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of a string"""
        if not text:
            return 0.0
        
        # Calculate character frequency
        freq = defaultdict(int)
        for char in text.lower():
            if char.isalnum():
                freq[char] += 1
        
        # Calculate entropy
        length = sum(freq.values())
        entropy = 0.0
        for count in freq.values():
            p = count / length
            entropy -= p * math.log2(p)
        
        return entropy
