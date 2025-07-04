"""
Distributed query executor for running optimized query plans
"""
import asyncio
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime
import aiohttp
import logging

from ..planner.query_planner import QueryPlan, ExecutionStep
from ..parser.sql_parser import QueryAST

@dataclass
class ExecutionResult:
    """Result of query execution"""
    query_id: str
    status: str  # success, error, partial
    results: List[Dict[str, Any]]
    execution_time_ms: float
    records_processed: int
    errors: List[str] = None

@dataclass
class NodeConnection:
    """Connection information for a query node"""
    node_id: str
    host: str
    port: int
    health_status: str = "unknown"

class QueryExecutor:
    """
    Executes distributed query plans across multiple nodes
    
    Handles:
    - Parallel execution of filter operations
    - Result aggregation and combination
    - Error handling and partial results
    - Performance monitoring
    """
    
    def __init__(self, node_connections: List[NodeConnection]):
        self.node_connections = {node.node_id: node for node in node_connections}
        self.logger = logging.getLogger(__name__)
        self.session = None
    
    async def execute_query(self, query_plan: QueryPlan, timeout_seconds: int = 30) -> ExecutionResult:
        """Execute complete query plan"""
        start_time = datetime.now()
        
        try:
            # Initialize HTTP session
            self.session = aiohttp.ClientSession()
            
            # Execute plan steps
            results = await self._execute_plan_steps(query_plan, timeout_seconds)
            
            # Combine results
            combined_results = await self._combine_results(results, query_plan)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ExecutionResult(
                query_id=query_plan.query_id,
                status="success",
                results=combined_results,
                execution_time_ms=execution_time,
                records_processed=len(combined_results)
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.error(f"Query execution failed: {str(e)}")
            
            return ExecutionResult(
                query_id=query_plan.query_id,
                status="error",
                results=[],
                execution_time_ms=execution_time,
                records_processed=0,
                errors=[str(e)]
            )
            
        finally:
            if self.session:
                await self.session.close()
    
    async def _execute_plan_steps(self, plan: QueryPlan, timeout: int) -> Dict[str, Any]:
        """Execute all steps in the query plan"""
        results = {}
        
        # Group steps by dependencies
        step_groups = self._group_steps_by_dependencies(plan.steps)
        
        # Execute steps in order
        for step_group in step_groups:
            group_results = await self._execute_step_group(step_group, timeout)
            results.update(group_results)
        
        return results
    
    async def _execute_step_group(self, steps: List[ExecutionStep], timeout: int) -> Dict[str, Any]:
        """Execute a group of independent steps in parallel"""
        tasks = []
        
        for step in steps:
            if step.step_type == "filter":
                task = self._execute_filter_step(step, timeout)
            elif step.step_type == "aggregate":
                task = self._execute_aggregate_step(step, timeout)
            else:
                task = self._execute_generic_step(step, timeout)
            
            tasks.append(task)
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Step {steps[i].step_id} failed: {result}")
                combined_results[steps[i].step_id] = {"error": str(result)}
            else:
                combined_results[steps[i].step_id] = result
        
        return combined_results
    
    async def _execute_filter_step(self, step: ExecutionStep, timeout: int) -> Dict[str, Any]:
        """Execute filter step on target partition"""
        partition_id = step.target_partitions[0]
        
        # For demonstration, simulate partition filtering
        # In real implementation, this would query the actual partition
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Generate mock filtered results
        mock_results = self._generate_mock_filter_results(step.operation)
        
        return {
            "partition_id": partition_id,
            "results": mock_results,
            "records_processed": len(mock_results),
            "execution_time_ms": 100
        }
    
    async def _execute_aggregate_step(self, step: ExecutionStep, timeout: int) -> Dict[str, Any]:
        """Execute aggregation step"""
        # Simulate aggregation processing
        await asyncio.sleep(0.05)
        
        # Generate mock aggregation results
        mock_results = self._generate_mock_aggregation_results(step.operation)
        
        return {
            "aggregation_type": step.operation.get("type", "unknown"),
            "results": mock_results,
            "records_processed": len(mock_results),
            "execution_time_ms": 50
        }
    
    async def _execute_generic_step(self, step: ExecutionStep, timeout: int) -> Dict[str, Any]:
        """Execute generic step"""
        await asyncio.sleep(0.02)
        
        return {
            "step_type": step.step_type,
            "results": [],
            "execution_time_ms": 20
        }
    
    def _group_steps_by_dependencies(self, steps: List[ExecutionStep]) -> List[List[ExecutionStep]]:
        """Group steps by their dependencies for parallel execution"""
        step_groups = []
        remaining_steps = steps.copy()
        completed_steps = set()
        
        while remaining_steps:
            # Find steps with no unmet dependencies
            ready_steps = []
            for step in remaining_steps:
                if all(dep in completed_steps for dep in step.dependencies):
                    ready_steps.append(step)
            
            if not ready_steps:
                # Handle circular dependencies or errors
                ready_steps = [remaining_steps[0]]
            
            step_groups.append(ready_steps)
            
            # Update completed steps
            for step in ready_steps:
                completed_steps.add(step.step_id)
                remaining_steps.remove(step)
        
        return step_groups
    
    async def _combine_results(self, step_results: Dict[str, Any], plan: QueryPlan) -> List[Dict[str, Any]]:
        """Combine results from all execution steps"""
        combined_results = []
        
        # Collect all filter results
        for step_id, result in step_results.items():
            if not isinstance(result, dict) or "error" in result:
                continue
            
            if "results" in result:
                combined_results.extend(result["results"])
        
        # Apply any final aggregations
        if any(step.step_type == "aggregate" for step in plan.steps):
            combined_results = self._apply_global_aggregation(combined_results, plan)
        
        return combined_results
    
    def _apply_global_aggregation(self, results: List[Dict[str, Any]], plan: QueryPlan) -> List[Dict[str, Any]]:
        """Apply global aggregation to combined results"""
        # This is a simplified implementation
        # In reality, you'd need to properly handle different aggregation types
        
        if not results:
            return []
        
        # For demonstration, return top 10 results
        return results[:10]
    
    def _generate_mock_filter_results(self, operation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock results for filter operations"""
        # Generate realistic log entries
        services = ["user-service", "payment-service", "inventory-service", "notification-service"]
        levels = ["INFO", "ERROR", "WARNING", "DEBUG"]
        
        results = []
        for i in range(20):  # Generate 20 mock entries
            result = {
                "timestamp": f"2025-01-{15 + i % 10:02d}T{10 + i % 14:02d}:00:00Z",
                "service": services[i % len(services)],
                "level": levels[i % len(levels)],
                "message": f"Mock log message {i}",
                "request_id": f"req-{1000 + i}",
                "response_time": 50 + (i * 10) % 500
            }
            results.append(result)
        
        return results
    
    def _generate_mock_aggregation_results(self, operation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock results for aggregation operations"""
        return [
            {"service": "user-service", "error_count": 45, "avg_response_time": 120},
            {"service": "payment-service", "error_count": 23, "avg_response_time": 250},
            {"service": "inventory-service", "error_count": 12, "avg_response_time": 80},
            {"service": "notification-service", "error_count": 8, "avg_response_time": 95}
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all connected nodes"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        health_results = {}
        
        for node_id, node in self.node_connections.items():
            try:
                # Simulate health check
                await asyncio.sleep(0.01)
                health_results[node_id] = {
                    "status": "healthy",
                    "response_time_ms": 10,
                    "last_check": datetime.now().isoformat()
                }
            except Exception as e:
                health_results[node_id] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
        
        return health_results
