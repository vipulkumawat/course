"""Coordinator for automated incident responses"""
import asyncio
import uuid
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from src.playbooks.engine.playbook_engine import PlaybookEngine, Playbook

logger = structlog.get_logger()


@dataclass
class SecurityEvent:
    """Security event that triggers incident response"""
    event_id: str
    event_type: str
    severity: str
    source: str
    timestamp: datetime
    details: Dict[str, Any]
    ioc_data: Optional[Dict[str, Any]] = None


class ResponseCoordinator:
    """Coordinates automated incident responses"""
    
    def __init__(self, playbook_engine: PlaybookEngine):
        self.playbook_engine = playbook_engine
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.active_responses: Dict[str, Dict] = {}
        self.response_history: List[Dict] = []
        self.running = False
        
    async def start(self):
        """Start the response coordinator"""
        self.running = True
        logger.info("response_coordinator_started")
        await self._process_events()
    
    async def stop(self):
        """Stop the response coordinator"""
        self.running = False
        logger.info("response_coordinator_stopped")
    
    async def handle_security_event(self, event: SecurityEvent) -> str:
        """Handle incoming security event"""
        await self.event_queue.put(event)
        logger.info("security_event_received",
                   event_id=event.event_id,
                   event_type=event.event_type,
                   severity=event.severity)
        return event.event_id
    
    async def _process_events(self):
        """Process security events from queue"""
        while self.running:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._respond_to_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.exception("event_processing_error", error=str(e))
    
    async def _respond_to_event(self, event: SecurityEvent):
        """Determine and execute appropriate response"""
        # Select playbooks based on event type and severity
        applicable_playbooks = self._select_playbooks(event)
        
        if not applicable_playbooks:
            logger.warning("no_applicable_playbooks", event_type=event.event_type)
            return
        
        # Execute playbooks (can run multiple in parallel for different aspects)
        execution_id = str(uuid.uuid4())
        
        response_info = {
            'execution_id': execution_id,
            'event_id': event.event_id,
            'event_type': event.event_type,
            'started_at': datetime.now().isoformat(),
            'playbooks': []
        }
        
        tasks = []
        for playbook_template in applicable_playbooks:
            # Create context from event data
            context = {
                'event_id': event.event_id,
                'event_type': event.event_type,
                'severity': event.severity,
                'source': event.source,
                **event.details
            }
            
            if event.ioc_data:
                context.update(event.ioc_data)
            
            # Create playbook from template
            playbook = self.playbook_engine.create_playbook_from_template(
                playbook_template, context
            )
            
            # Execute playbook
            task = asyncio.create_task(
                self.playbook_engine.execute_playbook(playbook, f"{execution_id}_{playbook.name}")
            )
            tasks.append(task)
            response_info['playbooks'].append(playbook.name)
        
        self.active_responses[execution_id] = response_info
        
        # Wait for all playbooks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        response_info['completed_at'] = datetime.now().isoformat()
        response_info['results'] = [
            r if not isinstance(r, Exception) else {'error': str(r)} 
            for r in results
        ]
        
        self.response_history.append(response_info)
        
        # Generate incident report
        try:
            incident_data = {
                'event_id': event.event_id,
                'event_type': event.event_type,
                'severity': event.severity,
                'timestamp': event.timestamp.isoformat(),
                'status': 'completed' if all(
                    isinstance(r, dict) and r.get('status') == 'completed' 
                    for r in response_info['results'] if not isinstance(r, Exception)
                ) else 'failed'
            }
            
            # Generate report for first playbook execution
            if response_info['results'] and isinstance(response_info['results'][0], dict):
                first_result = response_info['results'][0]
                if 'execution_id' in first_result:
                    report = self.playbook_engine.generate_incident_report(
                        first_result['execution_id'],
                        incident_data
                    )
                    response_info['incident_report'] = report
        except Exception as e:
            logger.warning("failed_to_generate_report", error=str(e))
        
        logger.info("incident_response_completed",
                   execution_id=execution_id,
                   playbooks=response_info['playbooks'])
    
    def _select_playbooks(self, event: SecurityEvent) -> List[str]:
        """Select applicable playbooks based on event"""
        playbooks = []
        
        # Map event types to playbook templates
        event_playbook_mapping = {
            'brute_force_attack': ['brute_force_response'],
            'malware_detected': ['malware_response'],
            'data_exfiltration': ['data_exfiltration_response'],
            'c2_communication': ['c2_communication_response'],
            'credential_stuffing': ['credential_protection_response'],
            'port_scan': ['network_scan_response']
        }
        
        # Add severity-based playbooks
        if event.severity == 'critical':
            playbooks.extend(event_playbook_mapping.get(event.event_type, []))
            if 'critical_incident_notification' not in playbooks:
                playbooks.append('critical_incident_notification')
        elif event.severity in ['high', 'medium']:
            playbooks.extend(event_playbook_mapping.get(event.event_type, []))
        
        return playbooks
    
    def get_response_status(self, execution_id: str) -> Optional[Dict]:
        """Get status of incident response"""
        return self.active_responses.get(execution_id)
    
    def get_response_history(self, limit: int = 100) -> List[Dict]:
        """Get response history"""
        return self.response_history[-limit:]
