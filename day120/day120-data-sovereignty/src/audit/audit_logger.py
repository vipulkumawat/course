"""Audit logging for compliance tracking"""
import json
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict

class ComplianceAuditLogger:
    def __init__(self):
        self.audit_log = []
        self.violations = []
    
    def log_classification(self, log_id: str, classification: Dict):
        """Log classification event"""
        self.audit_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'classification',
            'log_id': log_id,
            'classification': classification
        })
    
    def log_storage_decision(self, log_id: str, decision: Dict, target_region: str):
        """Log storage validation decision"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'storage_validation',
            'log_id': log_id,
            'target_region': target_region,
            'decision': decision
        }
        
        self.audit_log.append(event)
        
        if not decision.get('allowed'):
            self.violations.append(event)
    
    def log_transfer_decision(self, log_id: str, decision: Dict, 
                            source_region: str, target_region: str):
        """Log cross-border transfer decision"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'transfer_validation',
            'log_id': log_id,
            'source_region': source_region,
            'target_region': target_region,
            'decision': decision
        }
        
        self.audit_log.append(event)
        
        if not decision.get('allowed'):
            self.violations.append(event)
    
    def generate_compliance_report(self, hours: int = 24) -> Dict:
        """Generate compliance report for specified time window"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        
        recent_events = [
            e for e in self.audit_log 
            if e['timestamp'] > cutoff_str
        ]
        
        recent_violations = [
            v for v in self.violations
            if v['timestamp'] > cutoff_str
        ]
        
        # Aggregate by region
        storage_by_region = defaultdict(int)
        violations_by_region = defaultdict(int)
        
        for event in recent_events:
            if event['event_type'] == 'storage_validation':
                region = event.get('target_region', 'unknown')
                storage_by_region[region] += 1
        
        for violation in recent_violations:
            if 'target_region' in violation:
                region = violation['target_region']
                violations_by_region[region] += 1
        
        return {
            'report_period_hours': hours,
            'total_events': len(recent_events),
            'total_violations': len(recent_violations),
            'compliance_rate': (
                (len(recent_events) - len(recent_violations)) / len(recent_events) * 100
                if recent_events else 100.0
            ),
            'storage_by_region': dict(storage_by_region),
            'violations_by_region': dict(violations_by_region),
            'recent_violations': recent_violations[-10:]  # Last 10
        }
    
    def get_all_violations(self) -> List[Dict]:
        """Get all recorded violations"""
        return self.violations
