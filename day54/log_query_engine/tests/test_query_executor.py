"""
Tests for query executor functionality
"""
import pytest
import asyncio
from src.executor.query_executor import QueryExecutor, NodeConnection
from src.planner.query_planner import QueryPlan, ExecutionStep

class TestQueryExecutor:
    def setUp(self):
        self.node_connections = [
            NodeConnection("node1", "localhost", 8001),
            NodeConnection("node2", "localhost", 8002)
        ]
        self.executor = QueryExecutor(self.node_connections)
    
    @pytest.mark.asyncio
    async def test_simple_execution(self):
        executor = QueryExecutor(self.node_connections)
        
        # Create mock query plan
        plan = QueryPlan(
            query_id="test_query",
            steps=[
                ExecutionStep(
                    step_id="filter_1",
                    step_type="filter",
                    target_partitions=["partition_1"],
                    operation={"type": "local_filter", "conditions": []}
                )
            ],
            total_estimated_cost=100.0,
            parallelism_level=1
        )
        
        result = await executor.execute_query(plan)
        
        assert result.query_id == "test_query"
        assert result.status == "success"
        assert result.execution_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        executor = QueryExecutor(self.node_connections)
        
        health_status = await executor.health_check()
        
        assert isinstance(health_status, dict)
        assert "node1" in health_status
        assert "node2" in health_status
        
        for node_id, status in health_status.items():
            assert "status" in status
            assert "last_check" in status

if __name__ == "__main__":
    pytest.main([__file__])
