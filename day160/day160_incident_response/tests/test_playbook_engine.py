"""Tests for playbook engine"""
import pytest
import asyncio
from src.playbooks.engine.playbook_engine import PlaybookEngine, Action, Playbook, ActionStatus


class MockAction:
    async def execute(self, parameters, context):
        await asyncio.sleep(0.1)
        return {'success': True, 'message': 'Mock action executed'}


@pytest.mark.asyncio
async def test_playbook_execution():
    """Test basic playbook execution"""
    action_registry = {'mock_action': MockAction()}
    engine = PlaybookEngine(action_registry)
    
    action = Action(
        name='test_action',
        action_type='mock_action',
        parameters={'param1': 'value1'}
    )
    
    playbook = Playbook(
        name='test_playbook',
        description='Test playbook',
        severity='medium',
        triggers=['test'],
        actions=[action],
        metadata={'context': {}}
    )
    
    result = await engine.execute_playbook(playbook, 'test-exec-1')
    
    assert result['status'] == 'completed'
    assert len(result['actions']) == 1
    assert result['actions'][0]['status'] == 'success'


@pytest.mark.asyncio
async def test_action_retry():
    """Test action retry logic"""
    class FailingAction:
        def __init__(self):
            self.attempts = 0
        
        async def execute(self, parameters, context):
            self.attempts += 1
            if self.attempts < 3:
                raise Exception("Simulated failure")
            return {'success': True}
    
    failing_action = FailingAction()
    action_registry = {'failing': failing_action}
    engine = PlaybookEngine(action_registry)
    
    action = Action(
        name='retry_test',
        action_type='failing',
        parameters={},
        max_retries=3
    )
    
    playbook = Playbook(
        name='retry_playbook',
        description='Test retry',
        severity='low',
        triggers=['test'],
        actions=[action],
        metadata={'context': {}}
    )
    
    result = await engine.execute_playbook(playbook, 'retry-exec-1')
    
    assert failing_action.attempts == 3
    assert result['actions'][0]['status'] == 'success'


def test_condition_evaluation():
    """Test condition evaluation"""
    engine = PlaybookEngine({})
    
    conditions = [
        {'field': 'severity', 'operator': 'equals', 'value': 'high'}
    ]
    context = {'severity': 'high'}
    
    assert engine._evaluate_conditions(conditions, context) == True
    
    context = {'severity': 'low'}
    assert engine._evaluate_conditions(conditions, context) == False
