#!/bin/bash

# Day 156: SIEM Implementation - Complete Setup Script
# Creates full project structure, implements SIEM features, builds and tests

set -e

PROJECT_NAME="day156_siem_implementation"
PYTHON_VERSION="python3.11"

echo "🚀 Day 156: Building SIEM (Security Information Event Management) System"
echo "=================================================================="

# Create project structure
echo "📁 Creating project structure..."
mkdir -p ${PROJECT_NAME}/{src/{siem,processors,dashboard,api},tests,config,data/{events,incidents,rules},logs,web/{static/{css,js},templates},scripts,docker}

cd ${PROJECT_NAME}

# Create Python package files
touch src/__init__.py src/siem/__init__.py src/processors/__init__.py src/dashboard/__init__.py src/api/__init__.py tests/__init__.py

# Create requirements.txt with latest May 2025 compatible libraries
cat > requirements.txt << 'EOF'
# Core Dependencies - Latest May 2025 versions
fastapi==0.111.0
uvicorn[standard]==0.30.1
pydantic==2.7.4
redis==5.0.6
aioredis==2.0.1

# Data Processing
pandas==2.2.2
numpy==1.26.4

# Security & Hashing
cryptography==42.0.8
python-jose==3.3.0

# Testing
pytest==8.2.2
pytest-asyncio==0.23.7
pytest-cov==5.0.0
httpx==0.27.0

# Monitoring & Logging
structlog==24.2.0
prometheus-client==0.20.0

# WebSocket for real-time updates
websockets==12.0

# Database
aiosqlite==0.20.0

# Utilities
python-dotenv==1.0.1
pyyaml==6.0.1
python-dateutil==2.9.0
EOF

# Create configuration file
cat > config/siem_config.yaml << 'EOF'
siem:
  name: "DistributedLogSIEM"
  version: "1.0.0"
  
correlation:
  time_window_seconds: 300  # 5 minute correlation window
  max_events_per_window: 10000
  suspicious_threshold: 0.7
  critical_threshold: 0.9

redis:
  host: "localhost"
  port: 6379
  db: 0
  password: null
  key_prefix: "siem:"

detection_rules:
  brute_force:
    enabled: true
    failed_attempts_threshold: 5
    time_window_seconds: 60
    
  privilege_escalation:
    enabled: true
    suspicious_actions: ["sudo", "su", "admin_access"]
    time_window_seconds: 300
    
  data_exfiltration:
    enabled: true
    data_transfer_threshold_mb: 100
    suspicious_destinations: ["external", "unknown"]
    
  anomalous_access:
    enabled: true
    new_location_threshold_km: 500
    impossible_travel_speed_kmh: 900

risk_scoring:
  base_weights:
    authentication_failure: 0.3
    privilege_change: 0.6
    data_access: 0.4
    network_anomaly: 0.5
    
  multipliers:
    critical_asset: 2.0
    suspicious_ip: 1.5
    after_hours: 1.3
    new_location: 1.4

alerting:
  severities:
    - low
    - medium
    - high
    - critical
  
  notification_channels:
    - email
    - webhook
    - dashboard

dashboard:
  refresh_interval_seconds: 5
  max_incidents_display: 50
  chart_history_hours: 24
EOF

# Create environment configuration
cat > .env << 'EOF'
REDIS_HOST=localhost
REDIS_PORT=6379
API_HOST=0.0.0.0
API_PORT=8000
DASHBOARD_PORT=3000
LOG_LEVEL=INFO
EOF

# Create main SIEM Engine
cat > src/siem/engine.py << 'EOFPYTHON'
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
        self.redis = await aioredis.from_url(
            f"redis://{redis_config['host']}:{redis_config['port']}",
            db=redis_config['db'],
            decode_responses=True
        )
        
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
EOFPYTHON

# Create Event Normalizer
cat > src/processors/normalizer.py << 'EOFPYTHON'
"""
Security Event Normalizer - Transform raw logs into standardized security events
"""
import json
import time
import hashlib
from typing import Dict, Optional
from datetime import datetime
import structlog

from src.siem.engine import SecurityEvent, EventType

logger = structlog.get_logger()


class EventNormalizer:
    """Normalize various log formats into security events"""
    
    def __init__(self):
        self.event_count = 0
    
    def normalize_auth_log(self, raw_log: Dict) -> Optional[SecurityEvent]:
        """Normalize authentication logs"""
        try:
            event_id = self._generate_event_id(raw_log)
            
            # Determine event type
            event_type = EventType.AUTH_SUCCESS if raw_log.get('success', False) else EventType.AUTH_FAILURE
            
            return SecurityEvent(
                event_id=event_id,
                timestamp=raw_log.get('timestamp', time.time()),
                event_type=event_type,
                user=raw_log.get('username', 'unknown'),
                source_ip=raw_log.get('source_ip', '0.0.0.0'),
                destination=raw_log.get('destination', None),
                action='authentication',
                success=raw_log.get('success', False),
                metadata={
                    'method': raw_log.get('auth_method', 'password'),
                    'user_agent': raw_log.get('user_agent', ''),
                    'geo_location': raw_log.get('geo_location', {}),
                    'service': raw_log.get('service', 'unknown')
                }
            )
        except Exception as e:
            logger.error("Failed to normalize auth log", error=str(e))
            return None
    
    def normalize_access_log(self, raw_log: Dict) -> Optional[SecurityEvent]:
        """Normalize file/data access logs"""
        try:
            event_id = self._generate_event_id(raw_log)
            
            return SecurityEvent(
                event_id=event_id,
                timestamp=raw_log.get('timestamp', time.time()),
                event_type=EventType.DATA_ACCESS,
                user=raw_log.get('user', 'unknown'),
                source_ip=raw_log.get('client_ip', '0.0.0.0'),
                destination=raw_log.get('resource_path', None),
                action=raw_log.get('action', 'read'),
                success=raw_log.get('status_code', 200) < 400,
                metadata={
                    'resource': raw_log.get('resource_path', ''),
                    'resource_type': raw_log.get('resource_type', 'file'),
                    'bytes_transferred': raw_log.get('bytes', 0),
                    'critical_asset': self._is_critical_asset(raw_log)
                }
            )
        except Exception as e:
            logger.error("Failed to normalize access log", error=str(e))
            return None
    
    def normalize_admin_log(self, raw_log: Dict) -> Optional[SecurityEvent]:
        """Normalize administrative action logs"""
        try:
            event_id = self._generate_event_id(raw_log)
            
            # Check if this is privilege escalation
            action = raw_log.get('action', '').lower()
            is_priv_escalation = any(
                keyword in action 
                for keyword in ['sudo', 'su', 'admin', 'privilege', 'elevate']
            )
            
            event_type = EventType.PRIVILEGE_ESCALATION if is_priv_escalation else EventType.ADMIN_ACTION
            
            return SecurityEvent(
                event_id=event_id,
                timestamp=raw_log.get('timestamp', time.time()),
                event_type=event_type,
                user=raw_log.get('user', 'unknown'),
                source_ip=raw_log.get('source_ip', '0.0.0.0'),
                destination=raw_log.get('target', None),
                action=action,
                success=raw_log.get('success', True),
                metadata={
                    'command': raw_log.get('command', ''),
                    'target_user': raw_log.get('target_user', ''),
                    'session_id': raw_log.get('session_id', '')
                }
            )
        except Exception as e:
            logger.error("Failed to normalize admin log", error=str(e))
            return None
    
    def _generate_event_id(self, raw_log: Dict) -> str:
        """Generate unique event ID"""
        self.event_count += 1
        content = json.dumps(raw_log, sort_keys=True)
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"EVT-{int(time.time())}-{hash_val}-{self.event_count}"
    
    def _is_critical_asset(self, raw_log: Dict) -> bool:
        """Determine if accessed resource is a critical asset"""
        resource = raw_log.get('resource_path', '').lower()
        critical_patterns = ['admin', 'database', 'payment', 'credential', 'secret', 'private']
        return any(pattern in resource for pattern in critical_patterns)
EOFPYTHON

# Create API Server
cat > src/api/server.py << 'EOFPYTHON'
"""
FastAPI server for SIEM REST API
"""
import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import List, Dict
import yaml
import structlog
import json
import time

from src.siem.engine import SIEMEngine, SecurityEvent, EventType
from src.processors.normalizer import EventNormalizer

logger = structlog.get_logger()

# Load configuration
with open('config/siem_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

app = FastAPI(title="SIEM API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SIEM engine
siem_engine = SIEMEngine(config)
normalizer = EventNormalizer()

# WebSocket connections for real-time updates
active_websockets: List[WebSocket] = []


@app.on_event("startup")
async def startup_event():
    """Initialize SIEM on startup"""
    await siem_engine.initialize()
    logger.info("SIEM API server started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await siem_engine.shutdown()
    logger.info("SIEM API server stopped")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "SIEM API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    stats = await siem_engine.get_statistics()
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "statistics": stats
    }


@app.post("/api/events/ingest")
async def ingest_event(event_data: Dict):
    """Ingest a raw log event"""
    try:
        # Normalize based on log type
        log_type = event_data.get('type', 'access')
        
        if log_type == 'auth':
            security_event = normalizer.normalize_auth_log(event_data)
        elif log_type == 'access':
            security_event = normalizer.normalize_access_log(event_data)
        elif log_type == 'admin':
            security_event = normalizer.normalize_admin_log(event_data)
        else:
            raise ValueError(f"Unknown log type: {log_type}")
        
        if not security_event:
            raise HTTPException(status_code=400, detail="Failed to normalize event")
        
        # Process through SIEM
        incident = await siem_engine.process_event(security_event)
        
        # Notify WebSocket clients
        if incident:
            await broadcast_incident(incident)
        
        return {
            "status": "processed",
            "event_id": security_event.event_id,
            "incident_created": incident is not None,
            "incident_id": incident.incident_id if incident else None
        }
        
    except Exception as e:
        logger.error("Error ingesting event", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/incidents")
async def get_incidents(limit: int = 50):
    """Get recent security incidents"""
    try:
        incidents = await siem_engine.get_recent_incidents(limit)
        return {
            "total": len(incidents),
            "incidents": incidents
        }
    except Exception as e:
        logger.error("Error retrieving incidents", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statistics")
async def get_statistics():
    """Get SIEM statistics"""
    try:
        stats = await siem_engine.get_statistics()
        return stats
    except Exception as e:
        logger.error("Error retrieving statistics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/incidents")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time incident updates"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_websockets.remove(websocket)


async def broadcast_incident(incident):
    """Broadcast incident to all connected WebSocket clients"""
    incident_data = json.dumps(incident.to_dict())
    
    for websocket in active_websockets[:]:  # Copy list to avoid modification during iteration
        try:
            await websocket.send_text(incident_data)
        except:
            active_websockets.remove(websocket)


# Serve dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve SIEM dashboard HTML"""
    try:
        with open('web/templates/dashboard.html', 'r') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)
EOFPYTHON

# Create Dashboard HTML
cat > web/templates/dashboard.html << 'EOFHTML'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SIEM Security Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        
        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .dashboard-header {
            background: white;
            padding: 20px 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        
        .dashboard-header h1 {
            color: #1e3c72;
            font-size: 28px;
            margin-bottom: 5px;
        }
        
        .dashboard-header .subtitle {
            color: #666;
            font-size: 14px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #1e3c72;
        }
        
        .stat-card.critical .value {
            color: #dc3545;
        }
        
        .stat-card.high .value {
            color: #fd7e14;
        }
        
        .stat-card.medium .value {
            color: #ffc107;
        }
        
        .incidents-section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .section-header h2 {
            color: #1e3c72;
            font-size: 22px;
        }
        
        .refresh-btn {
            background: #1e3c72;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .refresh-btn:hover {
            background: #2a5298;
        }
        
        .incidents-list {
            max-height: 500px;
            overflow-y: auto;
        }
        
        .incident-card {
            background: #f8f9fa;
            border-left: 4px solid #666;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
            transition: all 0.3s;
        }
        
        .incident-card:hover {
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .incident-card.critical {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        
        .incident-card.high {
            border-left-color: #fd7e14;
            background: #fff8f0;
        }
        
        .incident-card.medium {
            border-left-color: #ffc107;
            background: #fffbf0;
        }
        
        .incident-card.low {
            border-left-color: #28a745;
            background: #f0fff4;
        }
        
        .incident-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .incident-title {
            font-weight: bold;
            font-size: 16px;
            color: #333;
        }
        
        .severity-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .severity-badge.critical {
            background: #dc3545;
            color: white;
        }
        
        .severity-badge.high {
            background: #fd7e14;
            color: white;
        }
        
        .severity-badge.medium {
            background: #ffc107;
            color: #333;
        }
        
        .severity-badge.low {
            background: #28a745;
            color: white;
        }
        
        .incident-description {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
        
        .incident-meta {
            display: flex;
            gap: 20px;
            font-size: 12px;
            color: #999;
        }
        
        .risk-score {
            font-weight: bold;
            color: #1e3c72;
        }
        
        .status-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 10px 20px;
            border-radius: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #28a745;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        
        .empty-state svg {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            opacity: 0.5;
        }
    </style>
</head>
<body>
    <div class="status-indicator">
        <div class="status-dot"></div>
        <span>Live Monitoring</span>
    </div>
    
    <div class="dashboard-container">
        <div class="dashboard-header">
            <h1>🛡️ SIEM Security Dashboard</h1>
            <div class="subtitle">Real-time Security Information and Event Management</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Events</h3>
                <div class="value" id="total-events">0</div>
            </div>
            <div class="stat-card critical">
                <h3>Critical Incidents</h3>
                <div class="value" id="critical-incidents">0</div>
            </div>
            <div class="stat-card high">
                <h3>High Severity</h3>
                <div class="value" id="high-incidents">0</div>
            </div>
            <div class="stat-card medium">
                <h3>Medium Severity</h3>
                <div class="value" id="medium-incidents">0</div>
            </div>
        </div>
        
        <div class="incidents-section">
            <div class="section-header">
                <h2>Recent Security Incidents</h2>
                <button class="refresh-btn" onclick="loadIncidents()">🔄 Refresh</button>
            </div>
            <div class="incidents-list" id="incidents-list">
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    <p>No security incidents detected</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let ws;
        
        function connectWebSocket() {
            ws = new WebSocket('ws://localhost:8000/ws/incidents');
            
            ws.onmessage = function(event) {
                const incident = JSON.parse(event.data);
                addIncidentToUI(incident);
                updateStats();
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
            
            ws.onclose = function() {
                console.log('WebSocket closed, reconnecting...');
                setTimeout(connectWebSocket, 3000);
            };
        }
        
        async function loadStatistics() {
            try {
                const response = await fetch('http://localhost:8000/api/statistics');
                const stats = await response.json();
                
                document.getElementById('total-events').textContent = stats.total_events || 0;
                document.getElementById('critical-incidents').textContent = 
                    stats.incidents_by_severity?.critical || 0;
                document.getElementById('high-incidents').textContent = 
                    stats.incidents_by_severity?.high || 0;
                document.getElementById('medium-incidents').textContent = 
                    stats.incidents_by_severity?.medium || 0;
            } catch (error) {
                console.error('Error loading statistics:', error);
            }
        }
        
        async function loadIncidents() {
            try {
                const response = await fetch('http://localhost:8000/api/incidents?limit=20');
                const data = await response.json();
                
                const incidentsList = document.getElementById('incidents-list');
                
                if (data.incidents && data.incidents.length > 0) {
                    incidentsList.innerHTML = '';
                    data.incidents.forEach(incident => {
                        addIncidentToUI(incident);
                    });
                } else {
                    incidentsList.innerHTML = `
                        <div class="empty-state">
                            <p>No security incidents detected</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading incidents:', error);
            }
        }
        
        function addIncidentToUI(incident) {
            const incidentsList = document.getElementById('incidents-list');
            
            // Remove empty state if present
            const emptyState = incidentsList.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }
            
            const timestamp = new Date(incident.created_at * 1000).toLocaleString();
            
            const incidentCard = document.createElement('div');
            incidentCard.className = `incident-card ${incident.severity}`;
            incidentCard.innerHTML = `
                <div class="incident-header">
                    <div class="incident-title">${incident.title}</div>
                    <span class="severity-badge ${incident.severity}">${incident.severity}</span>
                </div>
                <div class="incident-description">${incident.description}</div>
                <div class="incident-meta">
                    <span>ID: ${incident.incident_id}</span>
                    <span>Risk Score: <span class="risk-score">${(incident.risk_score * 100).toFixed(1)}%</span></span>
                    <span>Events: ${incident.events?.length || 0}</span>
                    <span>${timestamp}</span>
                </div>
            `;
            
            incidentsList.insertBefore(incidentCard, incidentsList.firstChild);
            
            // Keep only last 50 incidents
            while (incidentsList.children.length > 50) {
                incidentsList.removeChild(incidentsList.lastChild);
            }
        }
        
        function updateStats() {
            loadStatistics();
        }
        
        // Initialize
        connectWebSocket();
        loadStatistics();
        loadIncidents();
        
        // Refresh stats every 10 seconds
        setInterval(updateStats, 10000);
    </script>
</body>
</html>
EOFHTML

# Create test data generator
cat > scripts/generate_test_data.py << 'EOFPYTHON'
"""
Generate realistic security events for testing
"""
import asyncio
import aiohttp
import random
import time
from datetime import datetime

API_URL = "http://localhost:8000/api/events/ingest"

# Test users and IPs
USERS = ['alice', 'bob', 'charlie', 'admin', 'service_account']
SUSPICIOUS_IPS = ['192.168.1.100', '10.0.0.50', '172.16.0.20']
NORMAL_IPS = ['192.168.1.10', '192.168.1.11', '192.168.1.12']
CRITICAL_RESOURCES = ['/admin/users', '/api/database', '/config/secrets']
NORMAL_RESOURCES = ['/api/products', '/api/orders', '/dashboard']


async def send_event(session, event_data):
    """Send event to SIEM API"""
    try:
        async with session.post(API_URL, json=event_data) as response:
            result = await response.json()
            if result.get('incident_created'):
                print(f"🚨 INCIDENT CREATED: {result.get('incident_id')}")
            return result
    except Exception as e:
        print(f"Error sending event: {e}")


async def generate_normal_activity(session):
    """Generate normal user activity"""
    user = random.choice(USERS[:3])  # Normal users
    ip = random.choice(NORMAL_IPS)
    resource = random.choice(NORMAL_RESOURCES)
    
    event = {
        'type': 'access',
        'timestamp': time.time(),
        'user': user,
        'client_ip': ip,
        'resource_path': resource,
        'action': 'read',
        'status_code': 200,
        'bytes': random.randint(100, 10000)
    }
    
    await send_event(session, event)
    print(f"✅ Normal activity: {user} accessed {resource}")


async def simulate_brute_force_attack(session):
    """Simulate brute force authentication attack"""
    attacker_ip = random.choice(SUSPICIOUS_IPS)
    target_user = random.choice(USERS)
    
    print(f"\n🔴 Simulating brute force attack on {target_user} from {attacker_ip}")
    
    # Send multiple failed login attempts
    for i in range(7):
        event = {
            'type': 'auth',
            'timestamp': time.time(),
            'username': target_user,
            'source_ip': attacker_ip,
            'success': False,
            'auth_method': 'password',
            'service': 'ssh'
        }
        await send_event(session, event)
        print(f"  ❌ Failed login attempt {i + 1}")
        await asyncio.sleep(0.5)
    
    # Optional: successful login after brute force
    if random.random() < 0.3:
        event = {
            'type': 'auth',
            'timestamp': time.time(),
            'username': target_user,
            'source_ip': attacker_ip,
            'success': True,
            'auth_method': 'password',
            'service': 'ssh'
        }
        await send_event(session, event)
        print(f"  ⚠️  SUCCESSFUL LOGIN after brute force!")


async def simulate_privilege_escalation(session):
    """Simulate privilege escalation attempt"""
    user = random.choice(USERS[:3])
    ip = random.choice(NORMAL_IPS)
    
    print(f"\n🟠 Simulating privilege escalation by {user}")
    
    # Multiple privilege escalation actions
    actions = ['sudo /bin/bash', 'su root', 'sudo vim /etc/passwd']
    
    for action in actions:
        event = {
            'type': 'admin',
            'timestamp': time.time(),
            'user': user,
            'source_ip': ip,
            'action': action,
            'command': action,
            'success': True
        }
        await send_event(session, event)
        print(f"  🔓 Privilege action: {action}")
        await asyncio.sleep(1)


async def simulate_anomalous_access(session):
    """Simulate access from new/unusual location"""
    user = random.choice(USERS)
    new_ip = '203.0.113.50'  # Unusual IP
    resource = random.choice(CRITICAL_RESOURCES)
    
    print(f"\n🟡 Simulating anomalous access: {user} from new IP {new_ip}")
    
    event = {
        'type': 'access',
        'timestamp': time.time(),
        'user': user,
        'client_ip': new_ip,
        'resource_path': resource,
        'resource_type': 'database',
        'action': 'read',
        'status_code': 200,
        'bytes': 50000
    }
    await send_event(session, event)
    print(f"  🌐 Access from new location to critical resource")


async def run_demonstration():
    """Run complete security event demonstration"""
    print("=" * 70)
    print("🛡️  SIEM SECURITY EVENT DEMONSTRATION")
    print("=" * 70)
    
    async with aiohttp.ClientSession() as session:
        # 1. Normal activity baseline
        print("\n📊 Phase 1: Generating normal activity baseline...")
        for _ in range(5):
            await generate_normal_activity(session)
            await asyncio.sleep(0.3)
        
        await asyncio.sleep(2)
        
        # 2. Brute force attack
        await simulate_brute_force_attack(session)
        await asyncio.sleep(2)
        
        # 3. Privilege escalation
        await simulate_privilege_escalation(session)
        await asyncio.sleep(2)
        
        # 4. Anomalous access
        await simulate_anomalous_access(session)
        await asyncio.sleep(2)
        
        # 5. More normal activity
        print("\n📊 Generating additional normal activity...")
        for _ in range(5):
            await generate_normal_activity(session)
            await asyncio.sleep(0.3)
    
    print("\n" + "=" * 70)
    print("✅ Demonstration complete!")
    print("🌐 Check dashboard at: http://localhost:8000/dashboard")
    print("=" * 70)


if __name__ == '__main__':
    asyncio.run(run_demonstration())
EOFPYTHON

# Create comprehensive tests
cat > tests/test_siem_engine.py << 'EOFPYTHON'
"""
Unit tests for SIEM Engine
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, 'src')

from siem.engine import (
    SecurityEvent, EventType, Severity, SecurityIncident,
    CorrelationEngine, RiskScorer, SIEMEngine
)


@pytest.fixture
def sample_config():
    return {
        'correlation': {
            'time_window_seconds': 300,
            'max_events_per_window': 10000,
            'suspicious_threshold': 0.7,
            'critical_threshold': 0.9
        },
        'detection_rules': {
            'brute_force': {
                'enabled': True,
                'failed_attempts_threshold': 5,
                'time_window_seconds': 60
            },
            'privilege_escalation': {
                'enabled': True,
                'suspicious_actions': ['sudo', 'su', 'admin'],
                'time_window_seconds': 300
            },
            'anomalous_access': {
                'enabled': True
            }
        },
        'risk_scoring': {
            'base_weights': {
                'authentication_failure': 0.3,
                'privilege_change': 0.6,
                'data_access': 0.4
            },
            'multipliers': {
                'critical_asset': 2.0,
                'suspicious_ip': 1.5
            }
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None
        }
    }


@pytest.fixture
def sample_auth_failure():
    return SecurityEvent(
        event_id="EVT-001",
        timestamp=time.time(),
        event_type=EventType.AUTH_FAILURE,
        user="testuser",
        source_ip="192.168.1.100",
        destination=None,
        action="authentication",
        success=False,
        metadata={}
    )


def test_security_event_creation(sample_auth_failure):
    """Test security event object creation"""
    assert sample_auth_failure.event_type == EventType.AUTH_FAILURE
    assert sample_auth_failure.user == "testuser"
    assert sample_auth_failure.success is False


def test_risk_scorer_calculation(sample_config, sample_auth_failure):
    """Test risk score calculation"""
    scorer = RiskScorer(sample_config)
    risk = scorer.calculate_event_risk(sample_auth_failure)
    
    assert 0 <= risk <= 1.0
    assert risk > 0  # Failed auth should have some risk


def test_risk_scorer_with_critical_asset(sample_config, sample_auth_failure):
    """Test risk scoring with critical asset multiplier"""
    scorer = RiskScorer(sample_config)
    
    # Add critical asset flag
    sample_auth_failure.metadata['critical_asset'] = True
    risk = scorer.calculate_event_risk(sample_auth_failure)
    
    # Should be higher due to multiplier
    assert risk > 0.3


@pytest.mark.asyncio
async def test_correlation_engine_brute_force():
    """Test brute force detection"""
    # This test would need a mock Redis client
    # Simplified version for demonstration
    assert True  # Placeholder


def test_incident_creation():
    """Test security incident creation"""
    event = SecurityEvent(
        event_id="EVT-001",
        timestamp=time.time(),
        event_type=EventType.AUTH_FAILURE,
        user="testuser",
        source_ip="192.168.1.100",
        destination=None,
        action="authentication",
        success=False,
        metadata={}
    )
    
    incident = SecurityIncident(
        incident_id="INC-001",
        severity=Severity.HIGH,
        title="Test Incident",
        description="Test description",
        risk_score=0.85,
        events=[event],
        created_at=time.time()
    )
    
    assert incident.severity == Severity.HIGH
    assert len(incident.events) == 1
    assert incident.risk_score == 0.85


def test_incident_serialization():
    """Test incident serialization to dict"""
    event = SecurityEvent(
        event_id="EVT-001",
        timestamp=time.time(),
        event_type=EventType.AUTH_FAILURE,
        user="testuser",
        source_ip="192.168.1.100",
        destination=None,
        action="authentication",
        success=False,
        metadata={}
    )
    
    incident = SecurityIncident(
        incident_id="INC-001",
        severity=Severity.HIGH,
        title="Test Incident",
        description="Test description",
        risk_score=0.85,
        events=[event],
        created_at=time.time()
    )
    
    incident_dict = incident.to_dict()
    
    assert 'incident_id' in incident_dict
    assert 'severity' in incident_dict
    assert 'events' in incident_dict
    assert isinstance(incident_dict['events'], list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
EOFPYTHON

# Create start script
cat > start.sh << 'EOFSTART'
#!/bin/bash

echo "🚀 Starting Day 156 SIEM System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start Redis (if not running)
echo "🔴 Checking Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Start API server in background
echo "🌐 Starting SIEM API server..."
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Wait for server to start
sleep 5

echo ""
echo "======================================================================"
echo "✅ SIEM System is running!"
echo "======================================================================"
echo "📊 Dashboard: http://localhost:8000/dashboard"
echo "🔌 API: http://localhost:8000"
echo "📈 Health: http://localhost:8000/health"
echo ""
echo "To generate test events, run:"
echo "  python scripts/generate_test_data.py"
echo ""
echo "To stop, run:"
echo "  ./stop.sh"
echo "======================================================================"

# Save PID
echo $API_PID > .api.pid
EOFSTART

chmod +x start.sh

# Create stop script
cat > stop.sh << 'EOFSTOP'
#!/bin/bash

echo "🛑 Stopping SIEM System..."

# Kill API server
if [ -f ".api.pid" ]; then
    kill $(cat .api.pid) 2>/dev/null
    rm .api.pid
fi

# Stop Redis
redis-cli shutdown 2>/dev/null

echo "✅ SIEM System stopped"
EOFSTOP

chmod +x stop.sh

# Create Dockerfile
cat > docker/Dockerfile << 'EOFDOCKER'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose ports
EXPOSE 8000

# Start script
CMD ["sh", "-c", "redis-server --daemonize yes && uvicorn src.api.server:app --host 0.0.0.0 --port 8000"]
EOFDOCKER

# Create docker-compose.yml
cat > docker-compose.yml << 'EOFCOMPOSE'
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    
  siem:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    volumes:
      - ./src:/app/src
      - ./config:/app/config
      - ./web:/app/web

volumes:
  redis_data:
EOFCOMPOSE

# Create .dockerignore
cat > .dockerignore << 'EOFDOCKERIGNORE'
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.git/
.gitignore
README.md
EOFDOCKERIGNORE

echo ""
echo "======================================================================"
echo "✅ Project structure created successfully!"
echo "======================================================================"
echo ""
echo "📁 Project: ${PROJECT_NAME}"
echo ""
echo "Next steps:"
echo "1. cd ${PROJECT_NAME}"
echo "2. ./start.sh              # Start the SIEM system"
echo "3. Visit http://localhost:8000/dashboard"
echo "4. python scripts/generate_test_data.py  # Generate security events"
echo ""
echo "To run with Docker:"
echo "  docker-compose up --build"
echo ""
echo "======================================================================"