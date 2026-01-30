import re
from datetime import datetime
from typing import Dict, Optional

class SyslogParser:
    """Parse syslog format network logs"""
    
    # Syslog pattern: <priority>timestamp hostname process: message
    SYSLOG_PATTERN = r'<(\d+)>(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+):\s+(.*)'
    
    # Firewall log pattern
    FW_PATTERN = r'SRC=(\S+)\s+DST=(\S+)\s+.*PROTO=(\S+)\s+SPT=(\d+)\s+DPT=(\d+).*LEN=(\d+)'
    
    def parse(self, log_line: str) -> Optional[Dict]:
        """Parse a single log line"""
        try:
            # Match syslog format
            match = re.search(self.SYSLOG_PATTERN, log_line)
            if not match:
                return None
            
            priority, timestamp, hostname, process, message = match.groups()
            
            # Parse firewall message
            fw_match = re.search(self.FW_PATTERN, message)
            if not fw_match:
                return None
            
            src_ip, dst_ip, protocol, src_port, dst_port, length = fw_match.groups()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "source_ip": src_ip,
                "dest_ip": dst_ip,
                "source_port": int(src_port),
                "dest_port": int(dst_port),
                "protocol": protocol,
                "bytes": int(length),
                "hostname": hostname,
                "action": "ACCEPT" if "ACCEPT" in message else "DROP"
            }
        except Exception as e:
            print(f"Parse error: {e}")
            return None

class JSONParser:
    """Parse JSON format logs (AWS VPC, GCP)"""
    
    def parse(self, log_line: str) -> Optional[Dict]:
        """Parse JSON log entry"""
        try:
            import json
            data = json.loads(log_line)
            
            return {
                "timestamp": data.get("timestamp", datetime.now().isoformat()),
                "source_ip": data.get("srcaddr", ""),
                "dest_ip": data.get("dstaddr", ""),
                "source_port": int(data.get("srcport", 0)),
                "dest_port": int(data.get("dstport", 0)),
                "protocol": data.get("protocol", "TCP"),
                "bytes": int(data.get("bytes", 0)),
                "action": data.get("action", "ACCEPT")
            }
        except:
            return None

class DNSParser:
    """Parse DNS query logs"""
    
    DNS_PATTERN = r'client\s+(\S+)#(\d+).*query:\s+(\S+)\s+IN\s+(\S+)'
    
    def parse(self, log_line: str) -> Optional[Dict]:
        """Parse DNS log entry"""
        try:
            match = re.search(self.DNS_PATTERN, log_line)
            if not match:
                return None
            
            client_ip, client_port, domain, record_type = match.groups()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "source_ip": client_ip,
                "query_domain": domain,
                "query_type": record_type,
                "domain_length": len(domain)
            }
        except:
            return None
