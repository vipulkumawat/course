"""
Test suite for network traffic analysis system
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from parsers.syslog_parser import SyslogParser, JSONParser, DNSParser
from detectors.threat_detector import ThreatDetector
from analytics.traffic_analyzer import TrafficAnalyzer

def test_syslog_parser():
    """Test syslog parsing"""
    parser = SyslogParser()
    log = "<134>Jan 30 10:15:30 firewall kernel: [FILTER] SRC=192.168.1.10 DST=8.8.8.8 PROTO=TCP SPT=50000 DPT=53 LEN=60 ACCEPT"
    
    result = parser.parse(log)
    assert result is not None, "Failed to parse syslog"
    assert result["source_ip"] == "192.168.1.10", "Incorrect source IP"
    assert result["dest_ip"] == "8.8.8.8", "Incorrect dest IP"
    assert result["dest_port"] == 53, "Incorrect port"
    print("✓ Syslog parser test passed")

def test_port_scan_detection():
    """Test port scan detection"""
    detector = ThreatDetector()
    
    # Simulate port scan
    connections = []
    for port in range(1, 51):
        connections.append({
            "source_ip": "10.0.0.100",
            "dest_port": port,
            "bytes": 60
        })
    
    metrics = {"connections": connections}
    threats = detector.detect_threats(metrics)
    
    port_scan_threats = [t for t in threats if t["type"] == "port_scan"]
    assert len(port_scan_threats) > 0, "Failed to detect port scan"
    assert port_scan_threats[0]["threat_score"] >= 70, "Threat score too low"
    print("✓ Port scan detection test passed")

def test_dns_tunneling_detection():
    """Test DNS tunneling detection"""
    detector = ThreatDetector()
    
    # Suspicious DNS query (must be > 50 chars for detection)
    queries = [{
        "source_ip": "192.168.1.50",
        "query_domain": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6.evil.com"
    }]
    
    metrics = {"dns_queries": queries, "connections": [], "auth_attempts": [], "data_transfers": []}
    threats = detector.detect_threats(metrics)
    
    dns_threats = [t for t in threats if t["type"] == "dns_tunneling"]
    assert len(dns_threats) > 0, "Failed to detect DNS tunneling"
    print("✓ DNS tunneling detection test passed")

def test_traffic_analyzer():
    """Test traffic analyzer metrics"""
    analyzer = TrafficAnalyzer()
    
    # Add sample connections
    for i in range(100):
        analyzer.add_connection({
            "source_ip": f"192.168.1.{i % 50}",
            "dest_ip": "8.8.8.8",
            "dest_port": 443,
            "bytes": 1000,
            "protocol": "TCP"
        })
    
    metrics = analyzer.get_current_metrics()
    assert metrics["total_connections"] == 100, "Incorrect connection count"
    assert metrics["unique_sources"] > 0, "No unique sources detected"
    print("✓ Traffic analyzer test passed")

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*50)
    print("Running Network Traffic Analysis Tests")
    print("="*50 + "\n")
    
    try:
        test_syslog_parser()
        test_port_scan_detection()
        test_dns_tunneling_detection()
        test_traffic_analyzer()
        
        print("\n" + "="*50)
        print("✅ All tests passed!")
        print("="*50 + "\n")
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
