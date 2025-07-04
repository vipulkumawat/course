"""
Demo script for query engine functionality
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.parser.sql_parser import SQLParser
from src.planner.query_planner import QueryPlanner, PartitionInfo
from src.executor.query_executor import QueryExecutor, NodeConnection
from datetime import datetime

async def demo_query_engine():
    """Demonstrate query engine functionality"""
    print("🚀 Distributed Log Query Engine Demo")
    print("=" * 50)
    
    # Initialize components
    parser = SQLParser()
    
    # Create mock partition metadata
    partition_metadata = [
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
    
    planner = QueryPlanner(partition_metadata)
    
    # Mock node connections
    node_connections = [
        NodeConnection("node1", "localhost", 8001),
        NodeConnection("node2", "localhost", 8002)
    ]
    
    executor = QueryExecutor(node_connections)
    
    # Demo queries
    demo_queries = [
        "SELECT service, COUNT(*) as error_count FROM logs WHERE level = 'ERROR' AND timestamp > '2025-01-15' GROUP BY service ORDER BY error_count DESC LIMIT 10",
        "SELECT * FROM logs WHERE message CONTAINS 'timeout' AND timestamp > '2025-01-16' ORDER BY timestamp DESC LIMIT 5",
        "SELECT service, AVG(response_time) as avg_response FROM logs WHERE timestamp > '2025-01-15' GROUP BY service"
    ]
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n📝 Demo Query {i}:")
        print(f"Query: {query}")
        print("-" * 40)
        
        try:
            # Parse query
            ast = parser.parse(query)
            print(f"✅ Parsed successfully: {len(ast.select_fields)} fields, {len(ast.where_conditions)} conditions")
            
            # Create execution plan
            plan = planner.create_execution_plan(ast)
            print(f"📊 Execution plan: {len(plan.steps)} steps, parallelism level {plan.parallelism_level}")
            
            # Show optimizations
            if plan.optimization_notes:
                print("🔧 Optimizations applied:")
                for note in plan.optimization_notes:
                    print(f"   • {note}")
            
            # Execute query
            result = await executor.execute_query(plan)
            print(f"⚡ Execution completed in {result.execution_time_ms:.2f}ms")
            print(f"📋 Results: {result.records_processed} records processed")
            
            # Show sample results
            if result.results:
                print("📊 Sample results:")
                for j, record in enumerate(result.results[:3]):
                    print(f"   {j+1}. {record}")
                if len(result.results) > 3:
                    print(f"   ... and {len(result.results) - 3} more records")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n🎉 Demo completed successfully!")

if __name__ == "__main__":
    asyncio.run(demo_query_engine())
