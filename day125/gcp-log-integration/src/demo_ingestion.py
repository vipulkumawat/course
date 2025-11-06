"""Demo script to simulate log ingestion for testing"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from src.multi_project_manager import MultiProjectManager

async def simulate_log_ingestion(manager: MultiProjectManager, num_logs: int = 100):
    """Simulate log ingestion by updating stats directly"""
    print(f"Starting demo: simulating {num_logs} log entries...")
    
    # Initialize stats for demo projects
    demo_projects = [
        "your-production-project",
        "your-ml-project", 
        "your-analytics-project"
    ]
    
    for project_id in demo_projects:
        if project_id not in manager.stats:
            manager.stats[project_id] = {'ingested': 0, 'errors': 0}
    
    # Simulate log ingestion
    for i in range(num_logs):
        # Distribute logs across projects
        project_idx = i % len(demo_projects)
        project_id = demo_projects[project_idx]
        
        # Simulate processing a log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'severity': 'INFO' if i % 10 != 0 else 'ERROR',
            'project_id': project_id,
            'message': f'Demo log entry #{i}'
        }
        
        await manager.process_log(log_entry)
        manager.stats[project_id]['ingested'] += 1
        
        # Simulate occasional errors
        if i % 20 == 0:
            manager.stats[project_id]['errors'] += 1
        
        # Save stats periodically
        if i % 10 == 0:
            manager._save_stats()
            print(f"Processed {i+1}/{num_logs} logs...")
        
        await asyncio.sleep(0.1)  # Small delay to simulate real processing
    
    # Final stats save
    manager._save_stats()
    final_stats = manager.get_stats()
    print(f"\n✅ Demo complete!")
    print(f"Total ingested: {final_stats['total_ingested']}")
    print(f"Total errors: {final_stats['total_errors']}")
    print(f"By project: {final_stats['by_project']}")

if __name__ == "__main__":
    manager = MultiProjectManager()
    manager.load_config()
    
    # Initialize stats even if clients fail (for demo)
    for project in manager.projects:
        project_id = project['project_id']
        if project_id not in manager.stats:
            manager.stats[project_id] = {'ingested': 0, 'errors': 0}
    
    asyncio.run(simulate_log_ingestion(manager, num_logs=150))

