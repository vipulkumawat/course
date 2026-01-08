"""
Tests for GitOps Controller
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio


@pytest.fixture
def mock_config():
    return {
        'gitops': {'sync_interval': 30},
        'git': {
            'repository_url': 'https://github.com/test/repo.git',
            'branch': 'main'
        },
        'kubernetes': {'namespace': 'test-namespace'}
    }


@pytest.fixture
def mock_controller(mock_config):
    with patch('src.controller.gitops_controller.git.Repo'), \
         patch('src.controller.gitops_controller.config.load_kube_config'):
        from src.controller.gitops_controller import GitOpsController
        controller = GitOpsController(mock_config)
        controller.git_repo = Mock()
        controller.k8s_apps_v1 = Mock()
        controller.k8s_core_v1 = Mock()
        return controller


def test_controller_initialization(mock_controller):
    """Test controller can be initialized"""
    assert mock_controller is not None
    assert mock_controller.running == False


def test_load_git_manifests(mock_controller, tmp_path):
    """Test loading manifests from Git"""
    # Create temporary manifest file
    manifest_dir = tmp_path / "manifests" / "base"
    manifest_dir.mkdir(parents=True)
    
    manifest_file = manifest_dir / "test.yaml"
    manifest_file.write_text("""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  replicas: 2
""")
    
    mock_controller.git_repo.working_dir = str(tmp_path)
    manifests = mock_controller._load_git_manifests()
    
    assert "Deployment/test-deployment" in manifests
    assert manifests["Deployment/test-deployment"]['spec']['replicas'] == 2


def test_calculate_diff_create(mock_controller):
    """Test diff calculation for new resources"""
    git_state = {
        "Deployment/new-app": {
            'kind': 'Deployment',
            'metadata': {'name': 'new-app'},
            'spec': {'replicas': 2}
        }
    }
    cluster_state = {}
    
    changes = mock_controller._calculate_diff(git_state, cluster_state)
    
    assert len(changes) == 1
    assert changes[0]['action'] == 'create'
    assert changes[0]['resource'] == 'Deployment/new-app'


def test_calculate_diff_delete(mock_controller):
    """Test diff calculation for deleted resources"""
    git_state = {}
    cluster_state = {
        "Deployment/old-app": {'replicas': 2}
    }
    
    changes = mock_controller._calculate_diff(git_state, cluster_state)
    
    assert len(changes) == 1
    assert changes[0]['action'] == 'delete'
    assert changes[0]['resource'] == 'Deployment/old-app'


def test_resource_needs_update(mock_controller):
    """Test update detection"""
    manifest = {
        'kind': 'Deployment',
        'spec': {
            'replicas': 5,
            'template': {
                'spec': {
                    'containers': [{'image': 'app:v2.0'}]
                }
            }
        }
    }
    
    cluster_resource = {
        'replicas': 3,
        'image': 'app:v1.0'
    }
    
    needs_update = mock_controller._resource_needs_update(manifest, cluster_resource)
    assert needs_update == True


def test_get_status(mock_controller):
    """Test status reporting"""
    mock_controller.running = True
    mock_controller.last_sync_commit = "abc123def456"
    mock_controller.deployment_history = [
        {'commit': 'abc123', 'success': True}
    ]
    
    status = mock_controller.get_status()
    
    assert status['running'] == True
    assert status['last_sync_commit'] == 'abc123de'
    assert status['deployment_count'] == 1
