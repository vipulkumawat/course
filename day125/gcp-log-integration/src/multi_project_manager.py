"""Multi-Project Log Ingestion Manager"""
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import yaml
from src.gcp_client import GCPLoggingClient
import structlog

logger = structlog.get_logger()


class MultiProjectManager:
    """Orchestrates log ingestion from multiple GCP projects"""
    
    def __init__(self, config_path: str = "config/projects.yaml"):
        self.config_path = config_path
        self.projects: List[Dict] = []
        self.clients: Dict[str, GCPLoggingClient] = {}
        self.stats: Dict[str, Dict] = {}
        self.stats_file = Path("checkpoints/stats.json")
        
    def load_config(self):
        """Load project configurations from YAML"""
        with open(self.config_path) as f:
            config = yaml.safe_load(f)
            self.projects = [p for p in config['projects'] if p.get('enabled', True)]
            logger.info("config_loaded", project_count=len(self.projects))
    
    async def initialize_clients(self):
        """Authenticate all project clients"""
        for project in self.projects:
            project_id = project['project_id']
            credentials_path = project['credentials']
            
            client = GCPLoggingClient(project_id, credentials_path)
            if client.authenticate():
                self.clients[project_id] = client
                self.stats[project_id] = {'ingested': 0, 'errors': 0}
                logger.info("client_initialized", project_id=project_id)
            else:
                logger.error("client_init_failed", project_id=project_id)
    
    async def ingest_project_logs(self, project_config: Dict):
        """Ingest logs from a single project"""
        project_id = project_config['project_id']
        filter_expr = project_config['filter']
        client = self.clients.get(project_id)
        
        if not client:
            logger.error("client_not_found", project_id=project_id)
            return
        
        # Load checkpoint if exists
        checkpoint = self._load_checkpoint(project_id)
        
        try:
            async for log_entry in client.stream_logs(filter_expr, checkpoint):
                # Process log entry
                await self.process_log(log_entry)
                
                # Update stats
                self.stats[project_id]['ingested'] += 1
                self._save_stats()
                
                # Save checkpoint periodically
                if self.stats[project_id]['ingested'] % 100 == 0:
                    self._save_checkpoint(project_id, log_entry['timestamp'])
                    
        except Exception as e:
            logger.error("ingestion_error", project_id=project_id, error=str(e))
            self.stats[project_id]['errors'] += 1
            self._save_stats()
    
    async def process_log(self, log_entry: Dict):
        """Process individual log entry (override for custom logic)"""
        # Send to your log processing pipeline
        # This integrates with Days 31-36 message queue systems
        logger.info("log_processed", 
                   project_id=log_entry['project_id'],
                   severity=log_entry['severity'])
    
    def _load_checkpoint(self, project_id: str) -> Optional[str]:
        """Load last processed timestamp for project"""
        checkpoint_file = Path(f"checkpoints/{project_id}.json")
        if checkpoint_file.exists():
            with open(checkpoint_file) as f:
                data = json.load(f)
                return data.get('last_timestamp')
        return None
    
    def _save_checkpoint(self, project_id: str, timestamp: str):
        """Save processing checkpoint"""
        checkpoint_file = Path(f"checkpoints/{project_id}.json")
        checkpoint_file.parent.mkdir(exist_ok=True)
        with open(checkpoint_file, 'w') as f:
            json.dump({
                'project_id': project_id,
                'last_timestamp': timestamp,
                'updated_at': datetime.now().isoformat()
            }, f)
    
    async def run(self):
        """Start concurrent ingestion from all projects"""
        self.load_config()
        await self.initialize_clients()
        
        tasks = [
            self.ingest_project_logs(project)
            for project in self.projects
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def _save_stats(self):
        """Save stats to file for dashboard access"""
        self.stats_file.parent.mkdir(exist_ok=True)
        stats_data = self.get_stats()
        with open(self.stats_file, 'w') as f:
            json.dump(stats_data, f, indent=2)
    
    def get_stats(self) -> Dict:
        """Return current ingestion statistics"""
        return {
            'total_ingested': sum(s['ingested'] for s in self.stats.values()),
            'total_errors': sum(s['errors'] for s in self.stats.values()),
            'by_project': self.stats
        }


if __name__ == "__main__":
    manager = MultiProjectManager()
    asyncio.run(manager.run())
