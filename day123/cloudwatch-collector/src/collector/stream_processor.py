"""CloudWatch log stream processor."""
import boto3
import logging
from typing import List, Dict, Any, Optional, Callable
import time
from datetime import datetime
import json

from ..models.log_entry import CloudWatchLogEntry, LogGroupInfo


logger = logging.getLogger(__name__)


class StreamProcessor:
    """Processes CloudWatch log streams and extracts events."""
    
    def __init__(self, config: Dict[str, Any], state_manager):
        """Initialize stream processor."""
        self.config = config
        self.state_manager = state_manager
        self.clients = {}
        
    def get_client(self, region: str):
        """Get or create CloudWatch client for region."""
        if region not in self.clients:
            self.clients[region] = boto3.client(
                'logs',
                region_name=region,
                config=boto3.session.Config(
                    retries={'max_attempts': self.config['aws']['cloudwatch']['max_retries']},
                    max_pool_connections=self.config['aws']['cloudwatch']['max_connections']
                )
            )
        return self.clients[region]
    
    def get_log_streams(self, client, log_group: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get active log streams for a log group."""
        try:
            response = client.describe_log_streams(
                logGroupName=log_group,
                orderBy='LastEventTime',
                descending=True,
                limit=limit
            )
            return response.get('logStreams', [])
        except client.exceptions.ResourceNotFoundException:
            logger.warning(f"Log group not found: {log_group}")
            return []
        except Exception as e:
            logger.error(f"Failed to get log streams for {log_group}: {e}")
            return []
    
    def fetch_events(self, client, log_group: str, log_stream: str,
                    start_token: Optional[str] = None,
                    limit: int = 100) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Fetch events from a log stream."""
        try:
            params = {
                'logGroupName': log_group,
                'logStreamName': log_stream,
                'limit': limit,
                'startFromHead': False
            }
            
            if start_token:
                params['nextToken'] = start_token
            
            response = client.get_log_events(**params)
            
            events = response.get('events', [])
            next_token = response.get('nextForwardToken')
            
            return events, next_token
            
        except client.exceptions.ResourceNotFoundException:
            logger.warning(f"Log stream not found: {log_group}/{log_stream}")
            return [], None
        except client.exceptions.ThrottlingException:
            logger.warning(f"Throttled while fetching {log_group}/{log_stream}")
            time.sleep(self.config['aws']['cloudwatch']['retry_delay'])
            return [], start_token
        except Exception as e:
            logger.error(f"Failed to fetch events from {log_group}/{log_stream}: {e}")
            return [], start_token
    
    def process_log_group(self, log_group_info: LogGroupInfo,
                         callback: Callable[[List[CloudWatchLogEntry]], None],
                         max_streams: int = 10) -> int:
        """Process a log group and invoke callback with batched events."""
        client = self.get_client(log_group_info.region)
        log_group = log_group_info.log_group_name
        
        # Get active streams
        streams = self.get_log_streams(client, log_group, max_streams)
        total_processed = 0
        
        for stream in streams:
            stream_name = stream['logStreamName']
            state_key = f"{log_group_info.account_id}:{log_group_info.region}:{log_group}:{stream_name}"
            
            # Get last position
            last_token = self.state_manager.get_position(state_key)
            
            # Fetch events
            events, next_token = self.fetch_events(
                client, log_group, stream_name,
                last_token,
                self.config['collector']['batch_size']
            )
            
            if events:
                # Convert to CloudWatchLogEntry objects
                log_entries = [
                    CloudWatchLogEntry.from_cloudwatch_event(
                        event, log_group, stream_name,
                        log_group_info.region, log_group_info.account_id
                    )
                    for event in events
                ]
                
                # Apply filters
                if self.config['collector']['filters']['enabled']:
                    log_entries = self._apply_filters(log_entries)
                
                if log_entries:
                    # Invoke callback
                    callback(log_entries)
                    total_processed += len(log_entries)
                
                # Update position
                if next_token:
                    self.state_manager.update_position(state_key, next_token)
        
        return total_processed
    
    def _apply_filters(self, entries: List[CloudWatchLogEntry]) -> List[CloudWatchLogEntry]:
        """Apply filter patterns to log entries."""
        patterns = self.config['collector']['filters']['patterns']
        filtered = []
        
        for entry in entries:
            if any(pattern in entry.message for pattern in patterns):
                filtered.append(entry)
        
        return filtered
