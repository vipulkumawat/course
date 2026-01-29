"""Advanced features for incident response system"""
import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

logger = structlog.get_logger()


class IncidentState(Enum):
    """Enhanced lifecycle states for incidents"""
    DETECTED = "detected"
    ANALYZING = "analyzing"
    APPROVAL_PENDING = "approval_pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class ApprovalStatus(Enum):
    """Approval workflow status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class RiskScore:
    """Risk scoring for incidents"""
    base_score: int = 0
    severity_multiplier: float = 1.0
    asset_value: int = 0
    exposure_level: int = 0
    threat_intelligence: int = 0
    total_score: int = 0
    
    def calculate(self) -> int:
        """Calculate total risk score"""
        self.total_score = int(
            (self.base_score * self.severity_multiplier) +
            self.asset_value +
            (self.exposure_level * 2) +
            (self.threat_intelligence * 1.5)
        )
        return self.total_score


@dataclass
class SLA:
    """Performance SLA tracking"""
    target_response_time: int = 300  # seconds
    target_resolution_time: int = 3600  # seconds
    actual_response_time: Optional[float] = None
    actual_resolution_time: Optional[float] = None
    sla_met: bool = False
    sla_breached: bool = False
    
    def check_sla(self, response_time: float, resolution_time: Optional[float] = None) -> Dict[str, Any]:
        """Check if SLA is met"""
        self.actual_response_time = response_time
        if resolution_time:
            self.actual_resolution_time = resolution_time
        
        self.sla_met = response_time <= self.target_response_time
        if resolution_time:
            self.sla_met = self.sla_met and resolution_time <= self.target_resolution_time
        
        self.sla_breached = not self.sla_met
        
        return {
            'sla_met': self.sla_met,
            'sla_breached': self.sla_breached,
            'response_time': response_time,
            'target_response_time': self.target_response_time,
            'resolution_time': resolution_time,
            'target_resolution_time': self.target_resolution_time
        }


@dataclass
class ApprovalRequest:
    """Approval workflow request"""
    request_id: str
    action_name: str
    action_type: str
    parameters: Dict[str, Any]
    requested_by: str
    requested_at: datetime
    approvers: List[str]
    approvals: Dict[str, ApprovalStatus] = field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None
    
    def add_approval(self, approver: str, approved: bool, reason: Optional[str] = None):
        """Add an approval or rejection"""
        self.approvals[approver] = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        if reason:
            self.reason = reason
        
        # Check if all approvers have approved
        if all(status == ApprovalStatus.APPROVED for status in self.approvals.values()):
            self.status = ApprovalStatus.APPROVED
        elif any(status == ApprovalStatus.REJECTED for status in self.approvals.values()):
            self.status = ApprovalStatus.REJECTED
    
    def is_expired(self) -> bool:
        """Check if approval request has expired"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False


@dataclass
class ActionRollback:
    """Rollback information for an action"""
    action_id: str
    action_name: str
    action_type: str
    original_result: Dict[str, Any]
    rollback_actions: List[Dict[str, Any]] = field(default_factory=list)
    rolled_back: bool = False
    rollback_error: Optional[str] = None


class SafetyValidator:
    """Conditional safety logic validator"""
    
    @staticmethod
    def validate_action(action_type: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> tuple:
        """Validate action safety before execution"""
        # Critical action checks
        if action_type == 'isolate_system':
            system_id = parameters.get('system_id')
            if not system_id:
                return False, "System ID is required for isolation"
            
            # Check if system is already isolated
            if context.get('isolated_systems', {}).get(system_id):
                return False, f"System {system_id} is already isolated"
        
        if action_type == 'block_ip':
            ip_address = parameters.get('ip_address')
            if not ip_address:
                return False, "IP address is required for blocking"
            
            # Check if IP is in whitelist
            whitelist = context.get('ip_whitelist', [])
            if ip_address in whitelist:
                return False, f"IP {ip_address} is in whitelist and cannot be blocked"
        
        if action_type == 'suspend_account':
            user_id = parameters.get('user_id')
            if not user_id:
                return False, "User ID is required for suspension"
            
            # Check if user is admin
            if context.get('user_roles', {}).get(user_id) == 'admin':
                return False, f"Cannot suspend admin user {user_id} without explicit approval"
        
        return True, None
    
    @staticmethod
    def check_dry_run(action_type: str, context: Dict[str, Any]) -> bool:
        """Check if action should be run in dry-run mode"""
        return context.get('dry_run', False) and action_type in ['block_ip', 'isolate_system', 'suspend_account']


class StateMachine:
    """Lifecycle state machine for incidents"""
    
    VALID_TRANSITIONS = {
        IncidentState.DETECTED: [IncidentState.ANALYZING, IncidentState.CANCELLED],
        IncidentState.ANALYZING: [IncidentState.APPROVAL_PENDING, IncidentState.EXECUTING, IncidentState.CANCELLED],
        IncidentState.APPROVAL_PENDING: [IncidentState.APPROVED, IncidentState.CANCELLED],
        IncidentState.APPROVED: [IncidentState.EXECUTING, IncidentState.CANCELLED],
        IncidentState.EXECUTING: [IncidentState.PAUSED, IncidentState.COMPLETED, IncidentState.FAILED, IncidentState.ROLLING_BACK],
        IncidentState.PAUSED: [IncidentState.EXECUTING, IncidentState.CANCELLED, IncidentState.ROLLING_BACK],
        IncidentState.COMPLETED: [IncidentState.ROLLING_BACK],
        IncidentState.FAILED: [IncidentState.ROLLING_BACK, IncidentState.EXECUTING],
        IncidentState.ROLLING_BACK: [IncidentState.ROLLED_BACK, IncidentState.FAILED],
        IncidentState.ROLLED_BACK: [],
        IncidentState.CANCELLED: []
    }
    
    @staticmethod
    def can_transition(from_state: IncidentState, to_state: IncidentState) -> bool:
        """Check if state transition is valid"""
        return to_state in StateMachine.VALID_TRANSITIONS.get(from_state, [])
    
    @staticmethod
    def transition(current_state: IncidentState, new_state: IncidentState) -> tuple:
        """Attempt state transition"""
        if StateMachine.can_transition(current_state, new_state):
            return True, None
        return False, f"Invalid transition from {current_state.value} to {new_state.value}"


class IncidentReport:
    """Generate incident reports"""
    
    @staticmethod
    def generate_report(incident_data: Dict[str, Any], playbook_results: List[Dict], 
                       audit_log: List[Dict], risk_score: RiskScore, sla: SLA) -> Dict[str, Any]:
        """Generate comprehensive incident report"""
        report = {
            'incident_id': incident_data.get('event_id'),
            'incident_type': incident_data.get('event_type'),
            'severity': incident_data.get('severity'),
            'risk_score': risk_score.total_score,
            'detected_at': incident_data.get('timestamp'),
            'resolved_at': datetime.now().isoformat() if incident_data.get('status') == 'completed' else None,
            'duration_seconds': None,
            'sla_status': {
                'response_time_met': sla.sla_met,
                'response_time': sla.actual_response_time,
                'target_response_time': sla.target_response_time
            },
            'executed_playbooks': [r.get('playbook') for r in playbook_results],
            'actions_executed': len([log for log in audit_log if log.get('status') == 'success']),
            'actions_failed': len([log for log in audit_log if log.get('status') == 'failed']),
            'summary': IncidentReport._generate_summary(incident_data, playbook_results, audit_log),
            'timeline': IncidentReport._generate_timeline(audit_log),
            'recommendations': IncidentReport._generate_recommendations(incident_data, playbook_results)
        }
        
        if report['resolved_at']:
            start = datetime.fromisoformat(incident_data.get('timestamp'))
            end = datetime.fromisoformat(report['resolved_at'])
            report['duration_seconds'] = (end - start).total_seconds()
        
        return report
    
    @staticmethod
    def _generate_summary(incident_data: Dict, playbook_results: List[Dict], audit_log: List[Dict]) -> str:
        """Generate incident summary"""
        event_type = incident_data.get('event_type', 'unknown')
        severity = incident_data.get('severity', 'unknown')
        playbook_count = len(playbook_results)
        success_count = len([log for log in audit_log if log.get('status') == 'success'])
        
        return f"Incident of type {event_type} with {severity} severity was detected. " \
               f"{playbook_count} playbook(s) were executed with {success_count} successful actions."
    
    @staticmethod
    def _generate_timeline(audit_log: List[Dict]) -> List[Dict]:
        """Generate incident timeline"""
        timeline = []
        for entry in sorted(audit_log, key=lambda x: x.get('timestamp', '')):
            timeline.append({
                'timestamp': entry.get('timestamp'),
                'action': entry.get('action'),
                'status': entry.get('status'),
                'message': f"{entry.get('action')} - {entry.get('status')}"
            })
        return timeline
    
    @staticmethod
    def _generate_recommendations(incident_data: Dict, playbook_results: List[Dict]) -> List[str]:
        """Generate recommendations based on incident"""
        recommendations = []
        event_type = incident_data.get('event_type')
        
        if event_type == 'brute_force_attack':
            recommendations.append("Review authentication logs for additional compromised accounts")
            recommendations.append("Consider implementing rate limiting on authentication endpoints")
            recommendations.append("Enable multi-factor authentication for high-privilege accounts")
        
        elif event_type == 'malware_detected':
            recommendations.append("Perform full system scan on affected systems")
            recommendations.append("Review network traffic logs for exfiltration attempts")
            recommendations.append("Update antivirus signatures and security policies")
        
        elif event_type == 'c2_communication':
            recommendations.append("Conduct forensic analysis on affected systems")
            recommendations.append("Review all network connections from affected systems")
            recommendations.append("Check for additional compromised systems in the network")
        
        return recommendations
