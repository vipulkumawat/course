import re
import hashlib
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import structlog
from src.scanner.models import IOCIndicator, SecurityAlert, IOCType, Severity
from src.scanner.ioc_database import IOCDatabase

logger = structlog.get_logger()

class IOCMatcherEngine:
    """High-performance IOC matching engine"""
    
    def __init__(self, ioc_db: IOCDatabase, max_workers: int = 4):
        self.ioc_db = ioc_db
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Compiled patterns for extraction
        self.patterns = {
            "ip": re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            "domain": re.compile(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b', re.IGNORECASE),
            "sha256": re.compile(r'\b[A-Fa-f0-9]{64}\b'),
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        }
        
        self.stats = {
            "logs_scanned": 0,
            "matches_found": 0,
            "alerts_generated": 0
        }
    
    def extract_iocs_from_log(self, log_entry: Dict[str, Any]) -> List[tuple]:
        """Extract potential IOCs from log entry"""
        iocs = []
        
        # Convert log to text for pattern matching
        log_text = str(log_entry)
        
        # Extract IP addresses
        for ip in self.patterns["ip"].findall(log_text):
            iocs.append((ip, IOCType.IP_ADDRESS))
        
        # Extract domains
        for domain in self.patterns["domain"].findall(log_text):
            iocs.append((domain, IOCType.DOMAIN))
        
        # Extract file hashes
        for hash_val in self.patterns["sha256"].findall(log_text):
            iocs.append((hash_val, IOCType.FILE_HASH))
        
        # Extract emails
        for email in self.patterns["email"].findall(log_text):
            iocs.append((email, IOCType.EMAIL))
        
        return iocs
    
    def calculate_severity_score(self, matched_ioc: IOCIndicator, log_entry: Dict[str, Any]) -> float:
        """Calculate confidence score for match"""
        base_score = matched_ioc.confidence * 100
        
        # Adjust based on IOC severity
        severity_multipliers = {
            Severity.CRITICAL: 1.0,
            Severity.HIGH: 0.85,
            Severity.MEDIUM: 0.70,
            Severity.LOW: 0.55,
            Severity.INFO: 0.40
        }
        
        multiplier = severity_multipliers.get(matched_ioc.severity, 0.5)
        final_score = base_score * multiplier
        
        return min(final_score, 100.0)
    
    def scan_log(self, log_entry: Dict[str, Any]) -> List[SecurityAlert]:
        """Scan single log entry for IOC matches"""
        self.stats["logs_scanned"] += 1
        alerts = []
        
        try:
            # Extract IOCs from log
            potential_iocs = self.extract_iocs_from_log(log_entry)
            
            if not potential_iocs:
                return alerts
            
            # Batch lookup in database
            matches = self.ioc_db.batch_lookup(potential_iocs)
            
            # Generate alerts for matches
            for matched_ioc in matches:
                self.stats["matches_found"] += 1
                
                confidence_score = self.calculate_severity_score(matched_ioc, log_entry)
                
                alert = SecurityAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    matched_ioc=matched_ioc,
                    log_entry=log_entry,
                    severity=matched_ioc.severity,
                    confidence_score=confidence_score,
                    additional_context={
                        "extractor_version": "1.0",
                        "scan_timestamp": datetime.now().isoformat()
                    }
                )
                
                alerts.append(alert)
                self.stats["alerts_generated"] += 1
                
                logger.info("IOC match found",
                          ioc=matched_ioc.value,
                          type=matched_ioc.ioc_type.value,
                          severity=matched_ioc.severity.value,
                          confidence=confidence_score)
        
        except Exception as e:
            logger.error("Log scanning error", error=str(e), log_entry=log_entry)
        
        return alerts
    
    def scan_batch(self, log_entries: List[Dict[str, Any]]) -> List[SecurityAlert]:
        """Scan batch of logs concurrently"""
        all_alerts = []
        
        # Process logs in parallel
        futures = [self.executor.submit(self.scan_log, log) for log in log_entries]
        
        for future in futures:
            try:
                alerts = future.result()
                all_alerts.extend(alerts)
            except Exception as e:
                logger.error("Batch processing error", error=str(e))
        
        return all_alerts
    
    def get_stats(self) -> dict:
        """Get matcher statistics"""
        return {
            **self.stats,
            "match_rate": (self.stats["matches_found"] / self.stats["logs_scanned"] * 100)
                         if self.stats["logs_scanned"] > 0 else 0
        }
