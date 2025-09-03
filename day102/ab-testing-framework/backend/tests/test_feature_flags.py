import pytest
import asyncio
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from feature_flags.service import FeatureFlagService

@pytest.mark.asyncio
async def test_feature_flag_evaluation():
    service = FeatureFlagService()
    
    # Test consistent user assignment
    user_id = "test_user_123"
    flag_name = "test_feature"
    
    result1 = await service.evaluate_feature_flag(flag_name, user_id)
    result2 = await service.evaluate_feature_flag(flag_name, user_id)
    
    # Should be consistent
    assert result1 == result2

def test_user_experiment_hash():
    service = FeatureFlagService()
    
    # Test hash consistency
    hash1 = service._hash_user_experiment("user123", 456)
    hash2 = service._hash_user_experiment("user123", 456)
    
    assert hash1 == hash2
    assert 0 <= hash1 <= 1

@pytest.mark.asyncio
async def test_experiment_assignment():
    service = FeatureFlagService()
    
    # Mock database session
    class MockDB:
        def __init__(self):
            self.assignments = []
        def query(self, model):
            return self
        def filter(self, *args):
            return self
        def first(self):
            return None
        def add(self, assignment):
            self.assignments.append(assignment)
        def commit(self):
            pass
    
    db = MockDB()
    variant = await service.assign_user_to_experiment("user123", 1, db)
    
    assert variant in ["control", "treatment"]
    assert len(db.assignments) == 1
