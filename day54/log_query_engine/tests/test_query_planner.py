"""
Tests for query planner functionality
"""
import pytest
from datetime import datetime
from src.parser.sql_parser import SQLParser
from src.planner.query_planner import QueryPlanner, PartitionInfo

class TestQueryPlanner:
    def setUp(self):
        # Create mock partition metadata
        self.partition_metadata = [
            PartitionInfo(
                node_id="node1",
                partition_id="partition_2025_01_15",
                time_range=(datetime(2025, 1, 15), datetime(2025, 1, 16)),
                indexed_fields={"timestamp", "level", "service"},
                record_count=100000,
                size_bytes=50000000
            ),
            PartitionInfo(
                node_id="node2",
                partition_id="partition_2025_01_16",
                time_range=(datetime(2025, 1, 16), datetime(2025, 1, 17)),
                indexed_fields={"timestamp", "level", "service"},
                record_count=150000,
                size_bytes=75000000
            )
        ]
        
        self.planner = QueryPlanner(self.partition_metadata)
        self.parser = SQLParser()
    
    def test_partition_pruning(self):
        planner = QueryPlanner(self.partition_metadata)
        parser = SQLParser()
        
        query = "SELECT * FROM logs WHERE timestamp > '2025-01-15T12:00:00Z'"
        ast = parser.parse(query)
        plan = planner.create_execution_plan(ast)
        
        # Should create filter steps
        filter_steps = [step for step in plan.steps if step.step_type == "filter"]
        assert len(filter_steps) > 0
        
        # Should have optimization notes
        assert len(plan.optimization_notes) > 0
        assert any("partition pruning" in note.lower() for note in plan.optimization_notes)
    
    def test_aggregation_planning(self):
        planner = QueryPlanner(self.partition_metadata)
        parser = SQLParser()
        
        query = "SELECT service, COUNT(*) FROM logs GROUP BY service"
        ast = parser.parse(query)
        plan = planner.create_execution_plan(ast)
        
        # Should have aggregation step
        agg_steps = [step for step in plan.steps if step.step_type == "aggregate"]
        assert len(agg_steps) > 0
        
        # Should have local aggregation in filter operations
        filter_steps = [step for step in plan.steps if step.step_type == "filter"]
        for step in filter_steps:
            assert "local_aggregation" in step.operation
    
    def test_cost_estimation(self):
        planner = QueryPlanner(self.partition_metadata)
        parser = SQLParser()
        
        query = "SELECT * FROM logs WHERE level = 'ERROR'"
        ast = parser.parse(query)
        plan = planner.create_execution_plan(ast)
        
        # Should have estimated costs
        assert plan.total_estimated_cost > 0
        for step in plan.steps:
            assert step.estimated_cost >= 0

if __name__ == "__main__":
    pytest.main([__file__])
