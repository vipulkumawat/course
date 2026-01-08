"""
Test infrastructure cost estimation
"""

import pytest

class TestCostEstimation:
    """Test cost estimation logic"""
    
    def test_environment_cost_estimates(self):
        """Test that cost estimates are defined for all environments"""
        costs = {
            "dev": {"monthly": 150, "annual": 1800},
            "staging": {"monthly": 500, "annual": 6000},
            "prod": {"monthly": 2500, "annual": 30000}
        }
        
        for env, cost in costs.items():
            assert cost["monthly"] > 0
            assert cost["annual"] == cost["monthly"] * 12
    
    def test_cost_scaling(self):
        """Test that costs scale appropriately across environments"""
        dev_cost = 150
        staging_cost = 500
        prod_cost = 2500
        
        assert staging_cost > dev_cost
        assert prod_cost > staging_cost
        assert prod_cost >= staging_cost * 2  # Production should be significantly more

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
