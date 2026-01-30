import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from compliance.rule_engine import ComplianceRuleEngine, ComplianceFramework
from evidence.collector import EvidenceCollector
from reports.generator import ComplianceReportGenerator

def test_rule_engine_initialization():
    """Test rule engine initializes with default rules"""
    engine = ComplianceRuleEngine()
    assert len(engine.rules) > 0
    assert all(isinstance(rule.framework, ComplianceFramework) for rule in engine.rules)

def test_log_event_evaluation():
    """Test log event evaluation against rules"""
    engine = ComplianceRuleEngine()
    
    log_event = {
        "event_type": "auth_failure",
        "action": "account_locked",
        "user": "test@example.com"
    }
    
    matches = engine.evaluate_log_event(log_event)
    assert len(matches) > 0
    assert all("framework" in match for match in matches)

def test_compliance_coverage():
    """Test compliance coverage calculation"""
    engine = ComplianceRuleEngine()
    
    # Evaluate some events
    engine.evaluate_log_event({
        "event_type": "auth_failure",
        "action": "account_locked"
    })
    
    coverage = engine.get_compliance_coverage(ComplianceFramework.PCI_DSS)
    assert "coverage_percentage" in coverage
    assert coverage["coverage_percentage"] >= 0

def test_evidence_collection():
    """Test evidence collection and storage"""
    collector = EvidenceCollector("data/evidence")
    
    log_event = {"event_type": "test", "user": "test@example.com"}
    matches = [{"framework": "pci_dss", "requirement_id": "8.2.6"}]
    
    evidence_id = collector.collect(log_event, matches)
    assert evidence_id.startswith("EVD-")
    assert len(collector.evidence_store) > 0

def test_evidence_integrity():
    """Test evidence integrity verification"""
    collector = EvidenceCollector("data/evidence")
    
    log_event = {"event_type": "test"}
    matches = [{"framework": "soc2", "requirement_id": "CC6.1"}]
    
    collector.collect(log_event, matches)
    
    verification = collector.verify_all_integrity()
    assert verification["integrity_status"] == "PASS"

def test_gap_identification():
    """Test compliance gap identification"""
    engine = ComplianceRuleEngine()
    gaps = engine.identify_gaps(ComplianceFramework.PCI_DSS)
    
    # Initially all requirements should have gaps
    assert len(gaps) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
