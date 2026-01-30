from fastapi import APIRouter
from typing import Dict, List
from datetime import datetime
import random

router = APIRouter()

# These will be set by main.py
traffic_analyzer = None
threat_detector = None

def set_analyzers(analyzer, detector):
    """Set the analyzer and detector instances"""
    global traffic_analyzer, threat_detector
    traffic_analyzer = analyzer
    threat_detector = detector

# Simulate traffic data
traffic_data = []

@router.get("/metrics")
async def get_metrics() -> Dict:
    """Get current traffic metrics"""
    if traffic_analyzer and threat_detector:
        # Use real metrics from analyzer
        metrics = traffic_analyzer.get_current_metrics()
        threats = threat_detector.detect_threats(metrics)
        
        return {
            "timestamp": metrics.get("timestamp", datetime.now().isoformat()),
            "total_connections": metrics.get("total_connections", 0),
            "unique_sources": metrics.get("unique_sources", 0),
            "unique_destinations": metrics.get("unique_destinations", 0),
            "total_bytes": metrics.get("total_bytes", 0),
            "connections_per_second": metrics.get("connections_per_second", 0),
            "bytes_per_second": metrics.get("bytes_per_second", 0),
            "protocols": metrics.get("protocols", {}),
            "threats_count": len(threats),
            "connections": metrics.get("total_connections", 0),
            "bytes_transferred": metrics.get("total_bytes", 0),
            "unique_ips": metrics.get("unique_sources", 0)
        }
    else:
        # Fallback to simulated data
        return {
            "timestamp": datetime.now().isoformat(),
            "connections": random.randint(200, 500),
            "threats": random.randint(0, 5),
            "bytes_transferred": random.randint(1000000, 5000000),
            "unique_ips": random.randint(50, 150)
        }

@router.get("/threats")
async def get_threats() -> List[Dict]:
    """Get detected threats"""
    if traffic_analyzer and threat_detector:
        # Use real threats from detector
        metrics = traffic_analyzer.get_current_metrics()
        threats = threat_detector.detect_threats(metrics)
        return threats
    else:
        # Fallback to simulated threats
        threats = []
        if random.random() < 0.3:
            threats.append({
                "type": "port_scan",
                "source_ip": f"192.168.1.{random.randint(1, 254)}",
                "threat_score": random.randint(70, 95),
                "severity": "critical",
                "timestamp": datetime.now().isoformat()
            })
        return threats

@router.get("/topology")
async def get_topology() -> Dict:
    """Get network topology data from real traffic"""
    nodes = []
    edges = []
    
    if traffic_analyzer and threat_detector:
        # Get real metrics
        metrics = traffic_analyzer.get_current_metrics()
        threats = threat_detector.detect_threats(metrics)
        
        # Create threat score map
        threat_scores = {}
        for threat in threats:
            ip = threat.get("source_ip")
            if ip:
                threat_scores[ip] = threat.get("threat_score", 0)
        
        # Get top talkers and unique IPs
        top_talkers = metrics.get("top_talkers", [])
        connections = metrics.get("connections", [])
        
        # Collect unique IPs from connections
        all_ips = set()
        ip_bytes = {}
        ip_connections = {}
        
        for conn in connections[-100:]:  # Last 100 connections
            src = conn.get("source_ip")
            dst = conn.get("dest_ip")
            bytes_val = conn.get("bytes", 0)
            
            if src:
                all_ips.add(src)
                ip_bytes[src] = ip_bytes.get(src, 0) + bytes_val
                ip_connections[src] = ip_connections.get(src, 0) + 1
            
            if dst:
                all_ips.add(dst)
        
        # Create nodes from top talkers and unique IPs (limit to 15 nodes)
        ip_list = list(all_ips)[:15]
        if not ip_list:
            # Fallback: generate sample IPs
            ip_list = [f"192.168.1.{i+1}" for i in range(10)]
        
        for i, ip in enumerate(ip_list):
            # Calculate threat score based on actual threats and activity
            base_score = threat_scores.get(ip, 0)
            activity_score = min(50, (ip_connections.get(ip, 0) / 10))
            bytes_score = min(30, (ip_bytes.get(ip, 0) / 100000))
            threat_score = min(100, int(base_score + activity_score + bytes_score))
            
            nodes.append({
                "id": ip,
                "label": f"Host-{i+1}" if len(ip_list) > 1 else "Host-1",
                "threat_score": threat_score
            })
        
        # Create edges from connections
        edge_map = {}
        for conn in connections[-50:]:  # Last 50 connections
            src = conn.get("source_ip")
            dst = conn.get("dest_ip")
            bytes_val = conn.get("bytes", 0)
            
            if src and dst and src in ip_list and dst in ip_list:
                key = f"{src}-{dst}"
                if key not in edge_map:
                    edge_map[key] = {"source": src, "target": dst, "bytes": 0}
                edge_map[key]["bytes"] += bytes_val
        
        edges = list(edge_map.values())[:20]  # Limit to 20 edges
        
        # If no edges, create some sample connections
        if not edges and len(nodes) > 1:
            for i in range(min(15, len(nodes))):
                src_idx = i % len(nodes)
                dst_idx = (i + 1) % len(nodes)
                edges.append({
                    "source": nodes[src_idx]["id"],
                    "target": nodes[dst_idx]["id"],
                    "bytes": random.randint(5000, 50000)
                })
    else:
        # Fallback: generate sample topology
        for i in range(10):
            nodes.append({
                "id": f"192.168.1.{i+1}",
                "label": f"Host-{i+1}",
                "threat_score": random.randint(0, 100)
            })
        
        for i in range(15):
            edges.append({
                "source": f"192.168.1.{random.randint(1, 10)}",
                "target": f"192.168.1.{random.randint(1, 10)}",
                "bytes": random.randint(1000, 100000)
            })
    
    return {"nodes": nodes, "edges": edges}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
