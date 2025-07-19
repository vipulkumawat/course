import pytest
from unittest.mock import Mock, patch
from src.backend.services.erasure_coordinator import ErasureCoordinator
from src.backend.models.user_data import ErasureRequest

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def erasure_coordinator(mock_db):
    return ErasureCoordinator(mock_db)

@pytest.mark.asyncio
async def test_create_erasure_request(erasure_coordinator, mock_db):
    """Test creating an erasure request"""
    user_id = "test_user_123"
    request_type = "DELETE"
    
    # Mock database operations
    mock_db.add = Mock()
    mock_db.commit = Mock()
    
    with patch('asyncio.create_task'):
        request = await erasure_coordinator.create_erasure_request(user_id, request_type)
    
    assert request.user_id == user_id
    assert request.request_type == request_type
    assert request.status == "PENDING"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_process_erasure_request(erasure_coordinator, mock_db):
    """Test processing an erasure request"""
    request_id = "test_request_123"
    
    # Mock request object
    mock_request = Mock()
    mock_request.id = request_id
    mock_request.user_id = "test_user_123"
    mock_request.status = "PENDING"
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_request
    
    with patch.object(erasure_coordinator.data_tracker, 'get_user_data_locations', return_value=[]):
        await erasure_coordinator.process_erasure_request(request_id)
    
    assert mock_request.status == "COMPLETED"
