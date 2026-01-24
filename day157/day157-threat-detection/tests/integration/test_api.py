import pytest
from fastapi.testclient import TestClient
from src.main import load_rules_from_config
from src.engine.rule_engine import RuleEngine
from src.api.threat_api import ThreatDetectionAPI
from pathlib import Path

@pytest.fixture
def test_client():
    config_path = Path(__file__).parent.parent.parent / "config" / "rules_config.yaml"
    rules = load_rules_from_config(str(config_path))
    engine = RuleEngine(rules)
    api = ThreatDetectionAPI(engine)
    return TestClient(api.app)

def test_analyze_endpoint(test_client):
    """Test log analysis endpoint"""
    log_data = {
        "timestamp": "2025-06-16T10:00:00",
        "source_ip": "192.168.1.100",
        "endpoint": "/api/users",
        "method": "GET",
        "payload": "' UNION SELECT * FROM users",
        "user_agent": "Mozilla/5.0",
        "status_code": 200,
        "metadata": {"id": "test123"}
    }
    
    response = test_client.post("/api/analyze", json=log_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) > 0
    assert "classification" in data

def test_stats_endpoint(test_client):
    """Test statistics endpoint"""
    response = test_client.get("/api/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert "engine_stats" in data
    assert "classifier_stats" in data
