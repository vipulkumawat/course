"""GCP Cloud Logging Client Manager"""
import asyncio
from typing import AsyncGenerator, Dict, Optional
from datetime import datetime
from google.cloud import logging_v2
from google.oauth2 import service_account
from google.cloud.logging_v2 import types
import structlog

logger = structlog.get_logger()


class GCPLoggingClient:
    """Manages connection to GCP Cloud Logging API"""
    
    def __init__(self, project_id: str, credentials_path: str):
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.client: Optional[logging_v2.LoggingServiceV2Client] = None
        self._authenticated = False
        
    def authenticate(self) -> bool:
        """Initialize GCP client with service account credentials"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/logging.read']
            )
            self.client = logging_v2.LoggingServiceV2Client(credentials=credentials)
            self._authenticated = True
            logger.info("gcp_auth_success", project_id=self.project_id)
            return True
            
        except Exception as e:
            logger.error("gcp_auth_failed", project_id=self.project_id, error=str(e))
            return False
    
    async def stream_logs(
        self, 
        filter_expression: str,
        checkpoint: Optional[str] = None
    ) -> AsyncGenerator[Dict, None]:
        """Stream logs in real-time using tail API"""
        
        if not self._authenticated:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")
        
        # Build filter with checkpoint if provided
        if checkpoint:
            filter_expression += f' AND timestamp > "{checkpoint}"'
        
        request = types.ListLogEntriesRequest(
            resource_names=[f"projects/{self.project_id}"],
            filter=filter_expression,
            order_by="timestamp asc"
        )
        
        try:
            for entry in self.client.tail_log_entries([request]):
                for response in entry.entries:
                    yield self._normalize_log_entry(response)
                    
        except Exception as e:
            logger.error("log_stream_error", project_id=self.project_id, error=str(e))
            raise
    
    def _normalize_log_entry(self, entry: types.LogEntry) -> Dict:
        """Convert GCP log entry to normalized format"""
        return {
            'timestamp': entry.timestamp.isoformat() if entry.timestamp else None,
            'severity': entry.severity.name if entry.severity else 'DEFAULT',
            'message': entry.text_payload or entry.json_payload or entry.proto_payload,
            'resource': {
                'type': entry.resource.type,
                'labels': dict(entry.resource.labels) if entry.resource.labels else {}
            },
            'labels': dict(entry.labels) if entry.labels else {},
            'log_name': entry.log_name,
            'insert_id': entry.insert_id,
            'cloud_provider': 'gcp',
            'project_id': self.project_id
        }
