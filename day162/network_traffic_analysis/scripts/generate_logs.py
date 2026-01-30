#!/usr/bin/env python3
"""Generate sample network traffic logs"""

import random
import time
from datetime import datetime

def generate_firewall_log():
    """Generate syslog format firewall log"""
    src_ip = f"192.168.1.{random.randint(1, 254)}"
    dst_ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    protocol = random.choice(["TCP", "UDP", "ICMP"])
    src_port = random.randint(1024, 65535)
    dst_port = random.choice([80, 443, 22, 53, 3306, 5432, random.randint(1, 65535)])
    length = random.randint(40, 1500)
    action = random.choice(["ACCEPT", "ACCEPT", "ACCEPT", "DROP"])
    
    timestamp = datetime.now().strftime("%b %d %H:%M:%S")
    
    log = f"<134>{timestamp} firewall kernel: [FILTER] SRC={src_ip} DST={dst_ip} PROTO={protocol} SPT={src_port} DPT={dst_port} LEN={length} {action}"
    return log

def generate_port_scan():
    """Generate port scan traffic"""
    src_ip = f"10.0.0.{random.randint(1, 254)}"
    dst_ip = "192.168.1.100"
    
    logs = []
    for port in random.sample(range(1, 65535), 50):
        timestamp = datetime.now().strftime("%b %d %H:%M:%S")
        log = f"<134>{timestamp} firewall kernel: [FILTER] SRC={src_ip} DST={dst_ip} PROTO=TCP SPT={random.randint(50000, 60000)} DPT={port} LEN=60 DROP"
        logs.append(log)
    
    return logs

def main():
    print("Generating network traffic logs...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Generate normal traffic
            for _ in range(10):
                print(generate_firewall_log())
                time.sleep(0.1)
            
            # Occasionally generate port scan
            if random.random() < 0.05:
                print("\n--- Port Scan Detected ---")
                for log in generate_port_scan():
                    print(log)
                print("--- End Port Scan ---\n")
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nLog generation stopped")

if __name__ == "__main__":
    main()
