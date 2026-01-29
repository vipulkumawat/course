#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import time
import requests
import json
from colorama import init, Fore, Style

init(autoreset=True)

API_URL = "http://localhost:8000"

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{text:^60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

def demo_add_iocs():
    """Demonstrate adding IOCs"""
    print_header("Adding Sample IOCs")
    
    sample_iocs = [
        {
            "value": "192.168.1.100",
            "ioc_type": "ip_address",
            "severity": "high",
            "source": "demo",
            "description": "Known botnet IP"
        },
        {
            "value": "evil-domain.com",
            "ioc_type": "domain",
            "severity": "critical",
            "source": "demo",
            "description": "C2 server domain"
        },
        {
            "value": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "ioc_type": "file_hash",
            "severity": "high",
            "source": "demo",
            "description": "Malware hash"
        }
    ]
    
    for ioc in sample_iocs:
        try:
            response = requests.post(f"{API_URL}/ioc/add", json=ioc)
            if response.status_code == 200:
                print(f"{Fore.GREEN}✓{Style.RESET_ALL} Added: {ioc['value']} ({ioc['ioc_type']})")
            else:
                print(f"{Fore.RED}✗{Style.RESET_ALL} Failed: {ioc['value']}")
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
    
    time.sleep(1)

def demo_scan_logs():
    """Demonstrate log scanning"""
    print_header("Scanning Sample Logs")
    
    test_logs = [
        {
            "id": 1,
            "ip": "192.168.1.100",
            "action": "login_attempt",
            "user": "admin",
            "timestamp": time.time()
        },
        {
            "id": 2,
            "ip": "8.8.8.8",
            "action": "dns_query",
            "domain": "google.com",
            "timestamp": time.time()
        },
        {
            "id": 3,
            "domain": "evil-domain.com",
            "action": "connection_attempt",
            "timestamp": time.time()
        },
        {
            "id": 4,
            "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "action": "file_upload",
            "timestamp": time.time()
        }
    ]
    
    try:
        response = requests.post(f"{API_URL}/scan", json={"logs": test_logs})
        result = response.json()
        
        print(f"Scanned: {result['scanned']} logs")
        print(f"Alerts: {result['alert_count']}\n")
        
        if result['alerts']:
            for alert in result['alerts']:
                severity = alert['severity'].upper()
                color = Fore.RED if severity == 'CRITICAL' else Fore.YELLOW if severity == 'HIGH' else Fore.CYAN
                print(f"{color}[{severity}]{Style.RESET_ALL} IOC Detected: {alert['matched_ioc']['value']}")
                print(f"  Type: {alert['matched_ioc']['type']}")
                print(f"  Confidence: {alert['confidence_score']:.1f}%")
                print(f"  Description: {alert['matched_ioc']['description']}\n")
    
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

def show_stats():
    """Display system statistics"""
    print_header("System Statistics")
    
    try:
        response = requests.get(f"{API_URL}/stats")
        stats = response.json()
        
        print(f"{Fore.GREEN}IOC Database:{Style.RESET_ALL}")
        db_stats = stats['ioc_database']
        print(f"  Total IOCs: {db_stats['total_iocs']}")
        print(f"  Lookups: {db_stats['lookups']}")
        print(f"  Cache Hit Rate: {db_stats.get('cache_hit_rate', 0):.1f}%\n")
        
        print(f"{Fore.GREEN}Matcher Engine:{Style.RESET_ALL}")
        matcher_stats = stats['matcher']
        print(f"  Logs Scanned: {matcher_stats['logs_scanned']}")
        print(f"  Matches Found: {matcher_stats['matches_found']}")
        print(f"  Alerts Generated: {matcher_stats['alerts_generated']}\n")
    
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

def main():
    print(f"{Fore.CYAN}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         IOC Scanner System - Live Demonstration           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")
    
    # Wait for API to be ready
    print("Waiting for API server...")
    for _ in range(10):
        try:
            requests.get(f"{API_URL}/")
            print(f"{Fore.GREEN}✓ API server ready{Style.RESET_ALL}\n")
            break
        except:
            time.sleep(1)
    else:
        print(f"{Fore.RED}✗ API server not responding{Style.RESET_ALL}")
        return
    
    # Run demonstrations
    demo_add_iocs()
    time.sleep(2)
    
    # Run multiple scans to ensure metrics update
    print(f"\n{Fore.YELLOW}Running multiple scans to update metrics...{Style.RESET_ALL}")
    for i in range(3):
        demo_scan_logs()
        time.sleep(1)
    
    show_stats()
    
    # Verify metrics are non-zero
    print_header("Verifying Metrics")
    try:
        response = requests.get(f"{API_URL}/stats")
        stats = response.json()
        
        db_stats = stats.get('ioc_database', {})
        matcher_stats = stats.get('matcher', {})
        feed_stats = stats.get('feed_manager', {})
        
        issues = []
        if db_stats.get('total_iocs', 0) == 0:
            issues.append("Total IOCs is zero")
        if matcher_stats.get('logs_scanned', 0) == 0:
            issues.append("Logs scanned is zero")
        if matcher_stats.get('matches_found', 0) == 0:
            issues.append("Matches found is zero (expected if no IOCs match)")
        
        if issues:
            print(f"{Fore.YELLOW}⚠️  Warnings:{Style.RESET_ALL}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"{Fore.GREEN}✓ All metrics are updating correctly{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error verifying metrics: {e}{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}✅ Demonstration Complete!{Style.RESET_ALL}")
    print(f"\nView real-time dashboard at: {Fore.CYAN}http://localhost:3000{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
