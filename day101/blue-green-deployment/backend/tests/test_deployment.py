import pytest
import asyncio
from unittest.mock import Mock, patch
from app.core.deployment_controller import DeploymentController
from app.models.deployment import DeploymentRequest, Environment, DeploymentState

@pytest.fixture
def deployment_controller():
    controller = DeploymentController()
    controller.docker_client = Mock()
    return controller

@pytest.mark.asyncio
async def test_initialize_environments(deployment_controller):
    """Test environment initialization"""
    with patch.object(deployment_controller, '_start_environment') as mock_start:
        mock_start.return_value = None
        
        await deployment_controller.initialize_environments()
        
        assert mock_start.call_count == 2
        mock_start.assert_any_call(Environment.BLUE)
        mock_start.assert_any_call(Environment.GREEN)

@pytest.mark.asyncio
async def test_deployment_flow(deployment_controller):
    """Test complete deployment flow"""
    request = DeploymentRequest(version="2.0.0", config={"new_feature": True})
    
    with patch.object(deployment_controller, '_deploy_to_environment') as mock_deploy, \
         patch.object(deployment_controller, '_validate_environment_health') as mock_health, \
         patch.object(deployment_controller, '_switch_traffic') as mock_switch:
        
        # Mock successful health check
        mock_health.return_value.is_healthy = True
        
        result = await deployment_controller.deploy(request)
        
        assert result.state == DeploymentState.COMPLETED
        assert result.version == "2.0.0"
        assert mock_deploy.called
        assert mock_health.called
        assert mock_switch.called

def test_deployment_request_validation():
    """Test deployment request validation"""
    request = DeploymentRequest(version="1.0.0")
    assert request.version == "1.0.0"
    assert request.config == {}
    assert request.force == False
