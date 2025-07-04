"""
Distributed query planner for optimizing SQL queries across multiple nodes
"""
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json

from ..parser.sql_parser import QueryAST, WhereCondition, OperatorType

@dataclass
class PartitionInfo:
    """Information about a data partition"""
    node_id: str
    partition_id: str
    time_range: tuple  # (start_time, end_time)
    indexed_fields: Set[str]
    record_count: int
    size_bytes: int

@dataclass
class ExecutionStep:
    """Single step in query execution plan"""
    step_id: str
    step_type: str  # filter, aggregate, join, sort
    target_partitions: List[str]
    operation: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0

@dataclass
class QueryPlan:
    """Complete execution plan for distributed query"""
    query_id: str
    steps: List[ExecutionStep]
    total_estimated_cost: float
    parallelism_level: int
    optimization_notes: List[str] = field(default_factory=list)

class QueryPlanner:
    """
    Optimizes SQL queries for distributed execution across multiple nodes
    
    Key optimizations:
    - Partition pruning based on WHERE conditions
    - Predicate pushdown to reduce network traffic
    - Optimal join ordering
    - Aggregation distribution
    """
    
    def __init__(self, partition_metadata: List[PartitionInfo]):
        self.partition_metadata = partition_metadata
        self.optimization_rules = [
            self._partition_pruning,
            self._predicate_pushdown,
            self._aggregation_distribution,
            self._join_optimization
        ]
    
    def create_execution_plan(self, query_ast: QueryAST) -> QueryPlan:
        """Create optimized execution plan for query"""
        query_id = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start with basic plan
        plan = QueryPlan(
            query_id=query_id,
            steps=[],
            total_estimated_cost=0.0,
            parallelism_level=1
        )
        
        # Apply optimization rules
        for rule in self.optimization_rules:
            plan = rule(query_ast, plan)
        
        # Calculate final costs and parallelism
        plan.total_estimated_cost = sum(step.estimated_cost for step in plan.steps)
        plan.parallelism_level = len(set(
            partition for step in plan.steps 
            for partition in step.target_partitions
        ))
        
        return plan
    
    def _partition_pruning(self, query_ast: QueryAST, plan: QueryPlan) -> QueryPlan:
        """Eliminate partitions that can't contain relevant data"""
        relevant_partitions = self._find_relevant_partitions(query_ast.where_conditions)
        
        optimization_note = f"Partition pruning: {len(relevant_partitions)}/{len(self.partition_metadata)} partitions selected"
        plan.optimization_notes.append(optimization_note)
        
        # Create filter step for each relevant partition
        for partition in relevant_partitions:
            filter_step = ExecutionStep(
                step_id=f"filter_{partition.partition_id}",
                step_type="filter",
                target_partitions=[partition.partition_id],
                operation={
                    "type": "local_filter",
                    "conditions": [self._serialize_condition(cond) for cond in query_ast.where_conditions],
                    "fields": [field.name for field in query_ast.select_fields]
                },
                estimated_cost=self._estimate_filter_cost(partition, query_ast.where_conditions)
            )
            plan.steps.append(filter_step)
        
        return plan
    
    def _predicate_pushdown(self, query_ast: QueryAST, plan: QueryPlan) -> QueryPlan:
        """Push filter conditions down to storage layer"""
        # Already implemented in partition pruning
        plan.optimization_notes.append("Predicate pushdown: WHERE conditions pushed to storage layer")
        return plan
    
    def _aggregation_distribution(self, query_ast: QueryAST, plan: QueryPlan) -> QueryPlan:
        """Distribute aggregation operations across nodes"""
        if not query_ast.group_by and not any(field.aggregation for field in query_ast.select_fields):
            return plan
        
        # Add local aggregation steps
        for step in plan.steps:
            if step.step_type == "filter":
                step.operation["local_aggregation"] = {
                    "group_by": query_ast.group_by.fields if query_ast.group_by else [],
                    "aggregations": [
                        {"field": field.name, "function": field.aggregation}
                        for field in query_ast.select_fields
                        if field.aggregation
                    ]
                }
        
        # Add global aggregation step
        global_agg_step = ExecutionStep(
            step_id="global_aggregation",
            step_type="aggregate",
            target_partitions=["coordinator"],
            operation={
                "type": "global_aggregation",
                "group_by": query_ast.group_by.fields if query_ast.group_by else [],
                "aggregations": [
                    {"field": field.name, "function": field.aggregation}
                    for field in query_ast.select_fields
                    if field.aggregation
                ]
            },
            dependencies=[step.step_id for step in plan.steps if step.step_type == "filter"],
            estimated_cost=50.0  # Base cost for aggregation
        )
        plan.steps.append(global_agg_step)
        
        plan.optimization_notes.append("Aggregation distribution: Local + global aggregation strategy")
        return plan
    
    def _join_optimization(self, query_ast: QueryAST, plan: QueryPlan) -> QueryPlan:
        """Optimize join operations (placeholder for multi-table queries)"""
        # For now, we're dealing with single-table queries
        plan.optimization_notes.append("Join optimization: Single table query, no joins required")
        return plan
    
    def _find_relevant_partitions(self, conditions: List[WhereCondition]) -> List[PartitionInfo]:
        """Find partitions that might contain data matching WHERE conditions"""
        relevant_partitions = []
        
        for partition in self.partition_metadata:
            is_relevant = True
            
            # Check time-based conditions
            for condition in conditions:
                if condition.field == 'timestamp' and condition.operator in [
                    OperatorType.GREATER_THAN, OperatorType.GREATER_EQUAL,
                    OperatorType.LESS_THAN, OperatorType.LESS_EQUAL
                ]:
                    if not self._time_condition_matches_partition(condition, partition):
                        is_relevant = False
                        break
            
            if is_relevant:
                relevant_partitions.append(partition)
        
        return relevant_partitions
    
    def _time_condition_matches_partition(self, condition: WhereCondition, partition: PartitionInfo) -> bool:
        """Check if time condition could match data in partition"""
        try:
            condition_time = datetime.fromisoformat(condition.value.replace('Z', '+00:00'))
            partition_start, partition_end = partition.time_range
            
            if condition.operator == OperatorType.GREATER_THAN:
                return condition_time < partition_end
            elif condition.operator == OperatorType.GREATER_EQUAL:
                return condition_time <= partition_end
            elif condition.operator == OperatorType.LESS_THAN:
                return condition_time > partition_start
            elif condition.operator == OperatorType.LESS_EQUAL:
                return condition_time >= partition_start
            
        except (ValueError, TypeError):
            pass
        
        return True  # If we can't parse, assume it might match
    
    def _serialize_condition(self, condition: WhereCondition) -> Dict[str, Any]:
        """Serialize condition for execution"""
        return {
            "field": condition.field,
            "operator": condition.operator.value,
            "value": condition.value,
            "logical_operator": condition.logical_operator
        }
    
    def _estimate_filter_cost(self, partition: PartitionInfo, conditions: List[WhereCondition]) -> float:
        """Estimate cost of filtering operation on partition"""
        base_cost = partition.record_count * 0.001  # Base cost per record
        
        # Adjust for indexed fields
        for condition in conditions:
            if condition.field in partition.indexed_fields:
                base_cost *= 0.1  # Indexed fields are much faster
        
        return base_cost
    
    def estimate_query_performance(self, plan: QueryPlan) -> Dict[str, Any]:
        """Estimate query performance metrics"""
        parallel_steps = [step for step in plan.steps if step.step_type == "filter"]
        sequential_steps = [step for step in plan.steps if step.step_type != "filter"]
        
        parallel_time = max(step.estimated_cost for step in parallel_steps) if parallel_steps else 0
        sequential_time = sum(step.estimated_cost for step in sequential_steps)
        
        return {
            "estimated_execution_time_ms": parallel_time + sequential_time,
            "parallelism_level": len(parallel_steps),
            "network_operations": len([step for step in plan.steps if step.step_type == "aggregate"]),
            "optimization_summary": plan.optimization_notes
        }
