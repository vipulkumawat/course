import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from src.email_service.alert_evaluator import AlertEvaluator, AlertCondition, AlertSeverity, Alert

@pytest.fixture
def alert_evaluator():
    mock_redis = Mock()
    return AlertEvaluator(mock_redis)

@pytest.fixture
def sample_condition():
    return AlertCondition(
        name="Test Alert",
        threshold=5.0,
        metric_key="error_rate",
        severity=AlertSeverity.ERROR,
        cooldown_minutes=30
    )

def test_add_condition(alert_evaluator, sample_condition):
    """Test adding alert condition"""
    alert_evaluator.add_condition(sample_condition)
    
    assert "Test Alert" in alert_evaluator.conditions
    assert alert_evaluator.conditions["Test Alert"] == sample_condition

@pytest.mark.asyncio
async def test_evaluate_metrics_triggers_alert(alert_evaluator, sample_condition):
    """Test metric evaluation triggering alert"""
    alert_evaluator.add_condition(sample_condition)
    
    metrics = {"error_rate": 6.0}  # Above threshold
    
    alerts = await alert_evaluator.evaluate_metrics(metrics)
    
    assert len(alerts) == 1
    assert alerts[0].condition_name == "Test Alert"
    assert alerts[0].current_value == 6.0
    assert alerts[0].severity == AlertSeverity.ERROR

@pytest.mark.asyncio
async def test_evaluate_metrics_no_trigger(alert_evaluator, sample_condition):
    """Test metric evaluation not triggering alert"""
    alert_evaluator.add_condition(sample_condition)
    
    metrics = {"error_rate": 3.0}  # Below threshold
    
    alerts = await alert_evaluator.evaluate_metrics(metrics)
    
    assert len(alerts) == 0

def test_cooldown_period(alert_evaluator, sample_condition):
    """Test alert cooldown period"""
    alert_evaluator.add_condition(sample_condition)
    alert_evaluator.suppressed_alerts["Test Alert"] = datetime.now()
    
    # Should be in cooldown
    assert alert_evaluator._is_in_cooldown("Test Alert", 30) == True
    
    # Should not be in cooldown for old alerts
    alert_evaluator.suppressed_alerts["Test Alert"] = datetime.now() - timedelta(hours=1)
    assert alert_evaluator._is_in_cooldown("Test Alert", 30) == False

def test_get_alert_summary(alert_evaluator):
    """Test alert summary generation"""
    # Add some mock alerts
    alert1 = Alert("Test Alert 1", AlertSeverity.CRITICAL, 10.0, 5.0, "Test message", datetime.now())
    alert2 = Alert("Test Alert 2", AlertSeverity.WARNING, 3.0, 2.0, "Test message", datetime.now())
    
    alert_evaluator.alert_history = [alert1, alert2]
    
    summary = alert_evaluator.get_alert_summary()
    
    assert summary['total_alerts'] == 2
    assert summary['by_severity']['critical'] == 1
    assert summary['by_severity']['warning'] == 1
