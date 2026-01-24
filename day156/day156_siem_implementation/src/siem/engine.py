"""
SIEM Engine - Core correlation and detection logic
"""
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger()


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(str, Enum):
    AUTH_FAILURE = "auth_failure"
    AUTH_SUCCESS = "auth_success"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_ACCESS = "data_access"
    NETWORK_CONNECTION = "network_connection"
    FILE_ACCESS = "file_access"
    ADMIN_ACTION = "admin_action"


@dataclass
class SecurityEvent:
    """Normalized security event"""
    event_id: str
    timestamp: float
    event_type: EventType
    user: str
    source_ip: str
    destination: Optional[str]
    action: str
    success: bool
    metadata: Dict
    
    def to_dict(self):
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp,
            'event_type': self.event_type.value,
            'user': self.user,
            'source_ip': self.source_ip,
            'destination': self.destination,
            'action': self.action,
            'success': self.success,
            'metadata': self.metadata
        }


@dataclass
class SecurityIncident:
    """Security incident with correlated events"""
    incident_id: str
    severity: Severity
    title: str
    description: str
    risk_score: float
    events: List[SecurityEvent]
    created_at: float
    status: str = "open"
    
    def to_dict(self):
        return {
            'incident_id': self.incident_id,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'risk_score': self.risk_score,
            'events': [e.to_dict() for e in self.events],
            'created_at': self.created_at,
            'status': self.status
        }


class CorrelationEngine:
    """Real-time event correlation engine"""
    
    def __init__(self, redis_client: aioredis.Redis, config: Dict):
        self.redis = redis_client
        self.config = config
        self.time_window = config['correlation']['time_window_seconds']
        self.suspicious_threshold = config['correlation']['suspicious_threshold']
        
    async def correlate_events(self, event: SecurityEvent) -> Optional[SecurityIncident]:
        """Correlate new event with recent events to detect threats"""
        
        # Get recent events for this user
        user_events = await self._get_user_events(event.user)
        user_events.append(event)
        
        # Store event for future correlation
        await self._store_event(event)
        
        # Run correlation rules
        incident = await self._check_brute_force(user_events)
        if incident:
            return incident
            
        incident = await self._check_privilege_escalation(user_events)
        if incident:
            return incident
            
        incident = await self._check_anomalous_access(event, user_events)
        if incident:
            return incident
            
        return None
    
    async def _get_user_events(self, user: str) -> List[SecurityEvent]:
        """Retrieve recent events for a user from Redis"""
        key = f"siem:events:user:{user}"
        cutoff_time = time.time() - self.time_window
        
        # Get events from Redis sorted set
        event_data = await self.redis.zrangebyscore(
            key, cutoff_time, '+inf'
        )
        
        events = []
        for data in event_data:
            event_dict = json.loads(data)
            events.append(SecurityEvent(**event_dict))
        
        return events
    
    async def _store_event(self, event: SecurityEvent):
        """Store event in Redis for correlation"""
        key = f"siem:events:user:{event.user}"
        event_json = json.dumps(event.to_dict())
        
        # Add to sorted set with timestamp as score
        await self.redis.zadd(key, {event_json: event.timestamp})
        
        # Set expiration
        await self.redis.expire(key, self.time_window * 2)
        
        # Also store in global event stream
        await self.redis.xadd(
            'siem:event_stream',
            {'event': event_json},
            maxlen=100000
        )
    
    async def _check_brute_force(self, events: List[SecurityEvent]) -> Optional[SecurityIncident]:
        """Detect brute force authentication attempts"""
        rules = self.config['detection_rules']['brute_force']
        if not rules['enabled']:
            return None
        
        # Count failed auth attempts in window
        recent_time = time.time() - rules['time_window_seconds']
        failed_attempts = [
            e for e in events
            if e.event_type == EventType.AUTH_FAILURE
            and e.timestamp > recent_time
        ]
        
        if len(failed_attempts) >= rules['failed_attempts_threshold']:
            # Check if followed by success (successful breach)
            successful_auths = [
                e for e in events
                if e.event_type == EventType.AUTH_SUCCESS
                and e.timestamp > failed_attempts[-1].timestamp
            ]
            
            severity = Severity.CRITICAL if successful_auths else Severity.HIGH
            
            return SecurityIncident(
                incident_id=f"INC-{int(time.time() * 1000)}",
                severity=severity,
                title="Brute Force Attack Detected",
                description=f"User {events[0].user} had {len(failed_attempts)} failed login attempts "
                           f"from {failed_attempts[0].source_ip}",
                risk_score=0.85 if successful_auths else 0.75,
                events=failed_attempts + successful_auths,
                created_at=time.time()
            )
        
        return None
    
    async def _check_privilege_escalation(self, events: List[SecurityEvent]) -> Optional[SecurityIncident]:
        """Detect privilege escalation attempts"""
        rules = self.config['detection_rules']['privilege_escalation']
        if not rules['enabled']:
            return None
        
        recent_time = time.time() - rules['time_window_seconds']
        suspicious_actions = rules['suspicious_actions']
        
        # Look for privilege escalation actions
        priv_events = [
            e for e in events
            if e.timestamp > recent_time
            and any(action in e.action.lower() for action in suspicious_actions)
        ]
        
        if len(priv_events) >= 2:
            return SecurityIncident(
                incident_id=f"INC-{int(time.time() * 1000)}",
                severity=Severity.HIGH,
                title="Potential Privilege Escalation",
                description=f"User {events[0].user} performed {len(priv_events)} "
                           f"privilege escalation actions",
                risk_score=0.80,
                events=priv_events,
                created_at=time.time()
            )
        
        return None
    
    async def _check_anomalous_access(self, event: SecurityEvent, 
                                     user_events: List[SecurityEvent]) -> Optional[SecurityIncident]:
        """Detect anomalous access patterns"""
        rules = self.config['detection_rules']['anomalous_access']
        if not rules['enabled']:
            return None
        
        # Check for access from new location
        historical_ips = {e.source_ip for e in user_events[:-1]}
        
        if event.source_ip not in historical_ips and len(historical_ips) > 0:
            return SecurityIncident(
                incident_id=f"INC-{int(time.time() * 1000)}",
                severity=Severity.MEDIUM,
                title="Access from New Location",
                description=f"User {event.user} accessed from new IP {event.source_ip}",
                risk_score=0.65,
                events=[event],
                created_at=time.time()
            )
        
        return None


class RiskScorer:
    """Calculate risk scores for security events and incidents"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.weights = config['risk_scoring']['base_weights']
        self.multipliers = config['risk_scoring']['multipliers']
    
    def calculate_event_risk(self, event: SecurityEvent) -> float:
        """Calculate risk score for a single event"""
        base_score = 0.0
        
        # Base score from event type
        if event.event_type == EventType.AUTH_FAILURE:
            base_score = self.weights['authentication_failure']
        elif event.event_type == EventType.PRIVILEGE_ESCALATION:
            base_score = self.weights['privilege_change']
        elif event.event_type == EventType.DATA_ACCESS:
            base_score = self.weights['data_access']
        
        # Apply multipliers
        if not event.success:
            base_score *= 1.2
        
        if event.metadata.get('critical_asset'):
            base_score *= self.multipliers['critical_asset']
        
        if event.metadata.get('suspicious_ip'):
            base_score *= self.multipliers['suspicious_ip']
        
        return min(base_score, 1.0)
    
    def calculate_incident_risk(self, incident: SecurityIncident) -> float:
        """Calculate aggregated risk score for incident"""
        event_scores = [self.calculate_event_risk(e) for e in incident.events]
        avg_score = sum(event_scores) / len(event_scores) if event_scores else 0.0
        
        # Boost score based on event count (more events = higher risk)
        count_multiplier = min(1.0 + (len(incident.events) * 0.1), 2.0)
        
        return min(avg_score * count_multiplier, 1.0)


class SIEMEngine:
    """Main SIEM orchestration engine"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.redis = None
        self.correlation_engine = None
        self.risk_scorer = RiskScorer(config)
        self.incidents: List[SecurityIncident] = []
        self.running = False
        
    async def initialize(self):
        """Initialize SIEM components"""
        redis_config = self.config['redis']
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.redis = await aioredis.from_url(
                    f"redis://{redis_config['host']}:{redis_config['port']}",
                    db=redis_config['db'],
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # Test connection
                await self.redis.ping()
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Redis connection failed (attempt {attempt + 1}/{max_retries}), retrying...", error=str(e))
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to Redis after multiple attempts", error=str(e))
                    raise
        
        self.correlation_engine = CorrelationEngine(self.redis, self.config)
        logger.info("SIEM engine initialized")
    
    async def process_event(self, event: SecurityEvent) -> Optional[SecurityIncident]:
        """Process a security event through correlation engine"""
        logger.info("Processing security event", 
                   event_type=event.event_type, 
                   user=event.user)
        
        # Calculate event risk
        event_risk = self.risk_scorer.calculate_event_risk(event)
        event.metadata['risk_score'] = event_risk
        
        # Correlate with recent events
        incident = await self.correlation_engine.correlate_events(event)
        
        if incident:
            # Calculate incident risk
            incident.risk_score = self.risk_scorer.calculate_incident_risk(incident)
            
            # Store incident
            await self._store_incident(incident)
            self.incidents.append(incident)
            
            logger.warning("Security incident created",
                          incident_id=incident.incident_id,
                          severity=incident.severity,
                          risk_score=incident.risk_score)
            
            return incident
        
        return None
    
    async def _store_incident(self, incident: SecurityIncident):
        """Store incident in Redis"""
        key = f"siem:incidents:{incident.incident_id}"
        await self.redis.set(key, json.dumps(incident.to_dict()))
        await self.redis.expire(key, 86400 * 30)  # 30 days retention
        
        # Add to incidents list
        await self.redis.zadd(
            'siem:incidents:list',
            {incident.incident_id: incident.created_at}
        )
    
    async def get_recent_incidents(self, limit: int = 50) -> List[SecurityIncident]:
        """Retrieve recent incidents"""
        incident_ids = await self.redis.zrevrange('siem:incidents:list', 0, limit - 1)
        
        incidents = []
        for incident_id in incident_ids:
            key = f"siem:incidents:{incident_id}"
            data = await self.redis.get(key)
            if data:
                incident_dict = json.loads(data)
                # Reconstruct incident object (simplified)
                incidents.append(incident_dict)
        
        return incidents
    
    async def get_statistics(self) -> Dict:
        """Get SIEM statistics"""
        total_events = await self.redis.xlen('siem:event_stream')
        total_incidents = await self.redis.zcard('siem:incidents:list')
        
        # Get incident counts by severity
        incidents = await self.get_recent_incidents(1000)
        severity_counts = {s.value: 0 for s in Severity}
        for inc in incidents:
            severity_counts[inc['severity']] += 1
        
        return {
            'total_events': total_events,
            'total_incidents': total_incidents,
            'incidents_by_severity': severity_counts,
            'active_incidents': len([i for i in incidents if i['status'] == 'open'])
        }
    
    async def shutdown(self):
        """Cleanup resources"""
        if self.redis:
            await self.redis.close()
        logger.info("SIEM engine shutdown complete")
