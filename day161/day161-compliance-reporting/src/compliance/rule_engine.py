from typing import Dict, List, Any
from datetime import datetime
from enum import Enum
import json
import hashlib

class ComplianceFramework(Enum):
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"

class ComplianceRule:
    def __init__(self, rule_id: str, framework: ComplianceFramework, 
                 requirement_id: str, description: str, 
                 log_criteria: Dict[str, Any]):
        self.rule_id = rule_id
        self.framework = framework
        self.requirement_id = requirement_id
        self.description = description
        self.log_criteria = log_criteria
    
    def evaluate(self, log_event: Dict[str, Any]) -> bool:
        """Evaluate if log event satisfies rule criteria"""
        for key, expected in self.log_criteria.items():
            if key not in log_event:
                return False
            if isinstance(expected, list):
                if log_event[key] not in expected:
                    return False
            elif log_event[key] != expected:
                return False
        return True

class ComplianceRuleEngine:
    def __init__(self):
        self.rules: List[ComplianceRule] = []
        self.evidence_counts = {framework: {} for framework in ComplianceFramework}
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load predefined compliance rules"""
        # PCI-DSS Rules
        self.add_rule(ComplianceRule(
            "PCI_8.2.6",
            ComplianceFramework.PCI_DSS,
            "8.2.6",
            "Account lockout after failed login attempts",
            {"event_type": "auth_failure", "action": "account_locked"}
        ))
        
        self.add_rule(ComplianceRule(
            "PCI_10.2.1",
            ComplianceFramework.PCI_DSS,
            "10.2.1",
            "All user access to cardholder data logged",
            {"event_type": "data_access", "resource_type": "cardholder_data"}
        ))
        
        self.add_rule(ComplianceRule(
            "PCI_10.2.2",
            ComplianceFramework.PCI_DSS,
            "10.2.2",
            "All administrative actions logged",
            {"event_type": "admin_action", "privilege_level": "admin"}
        ))
        
        # SOC2 Rules
        self.add_rule(ComplianceRule(
            "SOC2_CC6.1",
            ComplianceFramework.SOC2,
            "CC6.1",
            "Logical access controls implemented",
            {"event_type": "access_control", "result": "enforced"}
        ))
        
        self.add_rule(ComplianceRule(
            "SOC2_CC7.2",
            ComplianceFramework.SOC2,
            "CC7.2",
            "System monitoring for anomalies",
            {"event_type": "security_alert", "severity": ["high", "critical"]}
        ))
        
        # ISO 27001 Rules
        self.add_rule(ComplianceRule(
            "ISO_A.9.4.2",
            ComplianceFramework.ISO27001,
            "A.9.4.2",
            "Secure log-on procedures",
            {"event_type": "authentication", "mfa_enabled": True}
        ))
        
        self.add_rule(ComplianceRule(
            "ISO_A.12.4.1",
            ComplianceFramework.ISO27001,
            "A.12.4.1",
            "Event logging and monitoring",
            {"event_type": "security_event", "logged": True}
        ))
        
        # HIPAA Rules
        self.add_rule(ComplianceRule(
            "HIPAA_164.308_a_1",
            ComplianceFramework.HIPAA,
            "164.308(a)(1)",
            "Security management process",
            {"event_type": "phi_access", "authorized": True}
        ))
        
        self.add_rule(ComplianceRule(
            "HIPAA_164.312_b",
            ComplianceFramework.HIPAA,
            "164.312(b)",
            "Audit controls",
            {"event_type": "audit_log", "phi_involved": True}
        ))
    
    def add_rule(self, rule: ComplianceRule):
        """Add compliance rule to engine"""
        self.rules.append(rule)
        if rule.requirement_id not in self.evidence_counts[rule.framework]:
            self.evidence_counts[rule.framework][rule.requirement_id] = 0
    
    def evaluate_log_event(self, log_event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate log event against all compliance rules"""
        matches = []
        for rule in self.rules:
            if rule.evaluate(log_event):
                self.evidence_counts[rule.framework][rule.requirement_id] += 1
                matches.append({
                    "rule_id": rule.rule_id,
                    "framework": rule.framework.value,
                    "requirement_id": rule.requirement_id,
                    "description": rule.description,
                    "timestamp": datetime.now().isoformat()
                })
        return matches
    
    def get_compliance_coverage(self, framework: ComplianceFramework) -> Dict[str, Any]:
        """Get compliance coverage statistics for framework"""
        total_requirements = len(self.evidence_counts[framework])
        requirements_with_evidence = sum(1 for count in self.evidence_counts[framework].values() if count > 0)
        
        return {
            "framework": framework.value,
            "total_requirements": total_requirements,
            "requirements_with_evidence": requirements_with_evidence,
            "coverage_percentage": (requirements_with_evidence / total_requirements * 100) if total_requirements > 0 else 0,
            "evidence_by_requirement": self.evidence_counts[framework]
        }
    
    def identify_gaps(self, framework: ComplianceFramework) -> List[str]:
        """Identify compliance requirements with no evidence"""
        return [req_id for req_id, count in self.evidence_counts[framework].items() if count == 0]
