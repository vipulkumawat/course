"""Core playbook engine for executing incident response procedures"""
import asyncio
import yaml
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.playbooks.advanced_features import (
    IncidentState, RiskScore, SLA, ApprovalRequest, ApprovalStatus,
    ActionRollback, SafetyValidator, StateMachine, IncidentReport
)

logger = structlog.get_logger()


class PlaybookStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ActionStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Action:
    """Individual action in a playbook"""
    name: str
    action_type: str
    parameters: Dict[str, Any]
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    timeout: int = 30
    retry_count: int = 0
    max_retries: int = 2
    status: ActionStatus = ActionStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    executed_at: Optional[datetime] = None


@dataclass
class Playbook:
    """Incident response playbook definition"""
    name: str
    description: str
    severity: str
    triggers: List[str]
    actions: List[Action]
    status: PlaybookStatus = PlaybookStatus.PENDING
    execution_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    lifecycle_state: IncidentState = IncidentState.DETECTED
    risk_score: Optional[RiskScore] = None
    sla: Optional[SLA] = None
    approval_requests: List[ApprovalRequest] = field(default_factory=list)
    rollback_actions: List[ActionRollback] = field(default_factory=list)


class PlaybookEngine:
    """Engine for executing security response playbooks"""
    
    def __init__(self, action_registry: Dict):
        self.action_registry = action_registry
        self.active_playbooks: Dict[str, Playbook] = {}
        self.playbook_templates: Dict[str, Dict] = {}
        self.audit_log: List[Dict] = []
        self.incident_reports: List[Dict] = []
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        
    def load_playbook_template(self, template_path: str) -> None:
        """Load playbook template from YAML"""
        with open(template_path, 'r') as f:
            template = yaml.safe_load(f)
            self.playbook_templates[template['name']] = template
            logger.info("playbook_template_loaded", name=template['name'])
    
    def create_playbook_from_template(self, template_name: str, 
                                     context: Dict[str, Any]) -> Playbook:
        """Create executable playbook from template"""
        if template_name not in self.playbook_templates:
            raise ValueError(f"Unknown playbook template: {template_name}")
        
        template = self.playbook_templates[template_name]
        
        # Create actions from template
        actions = []
        for action_def in template.get('actions', []):
            # Substitute context variables in parameters
            parameters = self._substitute_context(action_def.get('parameters', {}), context)
            
            action = Action(
                name=action_def['name'],
                action_type=action_def['type'],
                parameters=parameters,
                conditions=action_def.get('conditions', []),
                timeout=action_def.get('timeout', 30),
                max_retries=action_def.get('max_retries', 2)
            )
            actions.append(action)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(context, template.get('severity', 'medium'))
        
        # Initialize SLA
        sla = SLA(
            target_response_time=300 if template.get('severity') == 'critical' else 600,
            target_resolution_time=3600 if template.get('severity') == 'critical' else 7200
        )
        
        playbook = Playbook(
            name=template['name'],
            description=template['description'],
            severity=template.get('severity', 'medium'),
            triggers=template.get('triggers', []),
            actions=actions,
            metadata={'context': context, 'template': template_name},
            lifecycle_state=IncidentState.DETECTED,
            risk_score=risk_score,
            sla=sla
        )
        
        return playbook
    
    def _calculate_risk_score(self, context: Dict[str, Any], severity: str) -> RiskScore:
        """Calculate risk score for incident"""
        severity_multipliers = {
            'critical': 3.0,
            'high': 2.0,
            'medium': 1.5,
            'low': 1.0
        }
        
        risk_score = RiskScore(
            base_score=50,
            severity_multiplier=severity_multipliers.get(severity, 1.0),
            asset_value=context.get('asset_value', 0),
            exposure_level=context.get('exposure_level', 0),
            threat_intelligence=context.get('threat_intelligence_score', 0)
        )
        risk_score.calculate()
        return risk_score
    
    def _substitute_context(self, params: Dict, context: Dict) -> Dict:
        """Substitute context variables in parameters"""
        result = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                var_name = value[2:-1]
                result[key] = context.get(var_name, value)
            else:
                result[key] = value
        return result
    
    async def execute_playbook(self, playbook: Playbook, 
                              execution_id: str) -> Dict[str, Any]:
        """Execute a complete playbook"""
        playbook.execution_id = execution_id
        playbook.status = PlaybookStatus.RUNNING
        playbook.started_at = datetime.now()
        self.active_playbooks[execution_id] = playbook
        
        logger.info("playbook_execution_started", 
                   execution_id=execution_id,
                   playbook=playbook.name)
        
        execution_results = {
            'execution_id': execution_id,
            'playbook': playbook.name,
            'started_at': playbook.started_at.isoformat(),
            'actions': []
        }
        
        try:
            # Transition to analyzing state
            self._transition_state(playbook, IncidentState.ANALYZING)
            
            # Check if approval is required
            requires_approval = any(
                action.action_type in ['isolate_system', 'suspend_account', 'block_ip']
                for action in playbook.actions
            ) and playbook.metadata['context'].get('require_approval', False)
            
            if requires_approval:
                self._transition_state(playbook, IncidentState.APPROVAL_PENDING)
                approval_request = self._create_approval_request(playbook, execution_id)
                playbook.approval_requests.append(approval_request)
                self.pending_approvals[approval_request.request_id] = approval_request
                
                # Wait for approval (in real system, this would be async)
                logger.info("approval_required", execution_id=execution_id, request_id=approval_request.request_id)
                # For demo, auto-approve after short delay
                await asyncio.sleep(0.5)
                approval_request.add_approval("system", True, "Auto-approved for demo")
                self._transition_state(playbook, IncidentState.APPROVED)
            
            # Transition to executing
            self._transition_state(playbook, IncidentState.EXECUTING)
            
            for action in playbook.actions:
                # Check conditions
                if not self._evaluate_conditions(action.conditions, playbook.metadata['context']):
                    action.status = ActionStatus.SKIPPED
                    logger.info("action_skipped", action=action.name)
                    continue
                
                # Safety validation
                is_safe, safety_error = SafetyValidator.validate_action(
                    action.action_type, action.parameters, playbook.metadata['context']
                )
                if not is_safe:
                    action.status = ActionStatus.FAILED
                    action.error = safety_error
                    logger.warning("action_failed_safety_check", action=action.name, error=safety_error)
                    continue
                
                # Check if dry run
                if SafetyValidator.check_dry_run(action.action_type, playbook.metadata['context']):
                    action.status = ActionStatus.SUCCESS
                    action.result = {'dry_run': True, 'message': 'Action would be executed in production'}
                    logger.info("action_dry_run", action=action.name)
                    continue
                
                # Store rollback info before execution
                rollback = ActionRollback(
                    action_id=f"{execution_id}_{action.name}",
                    action_name=action.name,
                    action_type=action.action_type,
                    original_result={}
                )
                
                # Execute action with retry logic
                action_result = await self._execute_action_with_retry(
                    action, playbook.metadata['context']
                )
                
                # Store result for potential rollback
                rollback.original_result = action_result
                playbook.rollback_actions.append(rollback)
                
                execution_results['actions'].append({
                    'name': action.name,
                    'status': action.status.value,
                    'result': action.result,
                    'error': action.error
                })
                
                # Audit log entry
                self._log_action(execution_id, playbook.name, action)
                
                # Stop on critical failure
                if action.status == ActionStatus.FAILED and action.action_type in ['isolate_system', 'block_ip']:
                    logger.error("critical_action_failed", action=action.name)
                    playbook.status = PlaybookStatus.FAILED
                    break
            
            # Determine final status
            if playbook.status != PlaybookStatus.FAILED:
                failed_actions = [a for a in playbook.actions if a.status == ActionStatus.FAILED]
                if failed_actions:
                    playbook.status = PlaybookStatus.FAILED
                else:
                    playbook.status = PlaybookStatus.COMPLETED
            
        except Exception as e:
            logger.exception("playbook_execution_error", execution_id=execution_id)
            playbook.status = PlaybookStatus.FAILED
            execution_results['error'] = str(e)
        
        playbook.completed_at = datetime.now()
        execution_results['completed_at'] = playbook.completed_at.isoformat()
        execution_results['status'] = playbook.status.value
        execution_results['duration'] = (playbook.completed_at - playbook.started_at).total_seconds()
        
        # Check SLA
        if playbook.sla:
            sla_result = playbook.sla.check_sla(
                execution_results['duration'],
                execution_results['duration'] if playbook.status == PlaybookStatus.COMPLETED else None
            )
            execution_results['sla'] = sla_result
        
        # Update lifecycle state
        if playbook.status == PlaybookStatus.COMPLETED:
            self._transition_state(playbook, IncidentState.COMPLETED)
        elif playbook.status == PlaybookStatus.FAILED:
            self._transition_state(playbook, IncidentState.FAILED)
        
        # Add risk score and lifecycle state to results
        execution_results['risk_score'] = playbook.risk_score.total_score if playbook.risk_score else 0
        execution_results['lifecycle_state'] = playbook.lifecycle_state.value
        
        logger.info("playbook_execution_completed",
                   execution_id=execution_id,
                   status=playbook.status.value,
                   duration=execution_results['duration'],
                   sla_met=sla_result.get('sla_met', False) if playbook.sla else None)
        
        return execution_results
    
    def _transition_state(self, playbook: Playbook, new_state: IncidentState):
        """Transition playbook to new lifecycle state"""
        can_transition, error = StateMachine.transition(playbook.lifecycle_state, new_state)
        if can_transition:
            old_state = playbook.lifecycle_state
            playbook.lifecycle_state = new_state
            logger.info("state_transition", 
                       execution_id=playbook.execution_id,
                       from_state=old_state.value,
                       to_state=new_state.value)
        else:
            logger.warning("invalid_state_transition",
                         execution_id=playbook.execution_id,
                         from_state=playbook.lifecycle_state.value,
                         to_state=new_state.value,
                         error=error)
    
    def _create_approval_request(self, playbook: Playbook, execution_id: str) -> ApprovalRequest:
        """Create approval request for critical actions"""
        critical_actions = [a for a in playbook.actions 
                          if a.action_type in ['isolate_system', 'suspend_account', 'block_ip']]
        
        request_id = f"approval_{execution_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return ApprovalRequest(
            request_id=request_id,
            action_name="Critical Actions Execution",
            action_type="playbook_execution",
            parameters={'playbook': playbook.name, 'actions': [a.name for a in critical_actions]},
            requested_by="system",
            requested_at=datetime.now(),
            approvers=["security_team"],
            expires_at=datetime.now() + timedelta(hours=1)
        )
    
    async def rollback_playbook(self, execution_id: str) -> Dict[str, Any]:
        """Rollback a playbook execution"""
        playbook = self.active_playbooks.get(execution_id)
        if not playbook:
            raise ValueError(f"Playbook {execution_id} not found")
        
        self._transition_state(playbook, IncidentState.ROLLING_BACK)
        
        rollback_results = []
        for rollback in reversed(playbook.rollback_actions):
            if rollback.rolled_back:
                continue
            
            try:
                # In a real system, this would execute rollback actions
                # For now, we'll just mark as rolled back
                rollback.rolled_back = True
                rollback_results.append({
                    'action': rollback.action_name,
                    'status': 'rolled_back',
                    'message': f"Rolled back {rollback.action_name}"
                })
                logger.info("action_rolled_back", action=rollback.action_name)
            except Exception as e:
                rollback.rollback_error = str(e)
                rollback_results.append({
                    'action': rollback.action_name,
                    'status': 'rollback_failed',
                    'error': str(e)
                })
        
        self._transition_state(playbook, IncidentState.ROLLED_BACK)
        
        return {
            'execution_id': execution_id,
            'status': 'rolled_back',
            'rollback_results': rollback_results
        }
    
    def generate_incident_report(self, execution_id: str, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate incident report"""
        playbook = self.active_playbooks.get(execution_id)
        if not playbook:
            raise ValueError(f"Playbook {execution_id} not found")
        
        playbook_results = [{
            'playbook': playbook.name,
            'status': playbook.status.value,
            'execution_id': execution_id
        }]
        
        audit_log = self.get_audit_log(execution_id)
        
        report = IncidentReport.generate_report(
            incident_data,
            playbook_results,
            audit_log,
            playbook.risk_score,
            playbook.sla
        )
        
        self.incident_reports.append(report)
        return report
    
    def get_incident_reports(self, limit: int = 50) -> List[Dict]:
        """Get incident reports"""
        return self.incident_reports[-limit:]
    
    def approve_action(self, approval_request_id: str, approver: str, approved: bool, reason: Optional[str] = None):
        """Approve or reject an action"""
        approval = self.pending_approvals.get(approval_request_id)
        if not approval:
            raise ValueError(f"Approval request {approval_request_id} not found")
        
        approval.add_approval(approver, approved, reason)
        
        if approval.status == ApprovalStatus.APPROVED:
            # Find the playbook and transition to approved state
            for playbook in self.active_playbooks.values():
                if any(req.request_id == approval_request_id for req in playbook.approval_requests):
                    self._transition_state(playbook, IncidentState.APPROVED)
                    break
    
    async def _execute_action_with_retry(self, action: Action, 
                                        context: Dict) -> Dict[str, Any]:
        """Execute action with retry logic"""
        action.status = ActionStatus.EXECUTING
        
        while action.retry_count <= action.max_retries:
            try:
                action.executed_at = datetime.now()
                
                # Get executor from registry
                executor = self.action_registry.get(action.action_type)
                if not executor:
                    raise ValueError(f"Unknown action type: {action.action_type}")
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    executor.execute(action.parameters, context),
                    timeout=action.timeout
                )
                
                action.status = ActionStatus.SUCCESS
                action.result = result
                return result
                
            except asyncio.TimeoutError:
                error_msg = f"Action timeout after {action.timeout}s"
                action.error = error_msg
                logger.warning("action_timeout", action=action.name, retry=action.retry_count)
                
            except Exception as e:
                action.error = str(e)
                logger.warning("action_execution_failed", 
                             action=action.name,
                             error=str(e),
                             retry=action.retry_count)
            
            action.retry_count += 1
            if action.retry_count <= action.max_retries:
                await asyncio.sleep(2 ** action.retry_count)  # Exponential backoff
        
        # All retries exhausted
        action.status = ActionStatus.FAILED
        return {'error': action.error}
    
    def _evaluate_conditions(self, conditions: List[Dict], context: Dict) -> bool:
        """Evaluate action conditions"""
        if not conditions:
            return True
        
        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')
            
            context_value = context.get(field)
            
            if operator == 'equals' and context_value != value:
                return False
            elif operator == 'not_equals' and context_value == value:
                return False
            elif operator == 'greater_than' and not (context_value > value):
                return False
            elif operator == 'less_than' and not (context_value < value):
                return False
            elif operator == 'contains' and value not in str(context_value):
                return False
        
        return True
    
    def _log_action(self, execution_id: str, playbook_name: str, action: Action):
        """Log action execution for audit trail"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'execution_id': execution_id,
            'playbook': playbook_name,
            'action': action.name,
            'action_type': action.action_type,
            'status': action.status.value,
            'parameters': action.parameters,
            'result': action.result,
            'error': action.error,
            'retry_count': action.retry_count
        }
        self.audit_log.append(log_entry)
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        """Get status of a playbook execution"""
        playbook = self.active_playbooks.get(execution_id)
        if not playbook:
            return None
        
        return {
            'execution_id': execution_id,
            'playbook': playbook.name,
            'status': playbook.status.value,
            'started_at': playbook.started_at.isoformat() if playbook.started_at else None,
            'completed_at': playbook.completed_at.isoformat() if playbook.completed_at else None,
            'actions': [
                {
                    'name': a.name,
                    'status': a.status.value,
                    'error': a.error
                } for a in playbook.actions
            ]
        }
    
    def get_audit_log(self, execution_id: Optional[str] = None) -> List[Dict]:
        """Get audit log entries"""
        if execution_id:
            return [log for log in self.audit_log if log['execution_id'] == execution_id]
        return self.audit_log
