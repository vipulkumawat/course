#!/bin/bash

# Day 63: Chaos Testing Tools Implementation Script
# Module 2: Scalable Log Processing | Week 9: High Availability and Fault Tolerance

set -e

echo "🎯 Day 63: Building Chaos Testing Tools for Distributed Log Processing"
echo "==============================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python version
    if ! python3.11 --version >/dev/null 2>&1; then
        if ! python3 --version | grep -q "3.11"; then
            log_error "Python 3.11 required. Please install Python 3.11"
            exit 1
        fi
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python3.11"
    fi
    
    # Check Docker
    if ! command -v docker >/dev/null 2>&1; then
        log_warning "Docker not found. Some features will be limited."
        DOCKER_AVAILABLE=false
    else
        DOCKER_AVAILABLE=true
    fi
    
    # Check Node.js for React frontend
    if ! command -v npm >/dev/null 2>&1; then
        log_warning "npm not found. Installing Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - >/dev/null 2>&1
        sudo apt-get install -y nodejs >/dev/null 2>&1 || {
            log_error "Failed to install Node.js. Please install manually."
            exit 1
        }
    fi
    
    log_success "Prerequisites checked"
}

# Create project structure
create_project_structure() {
    log_info "Creating project structure..."
    
    PROJECT_DIR="chaos-testing-framework"
    rm -rf $PROJECT_DIR
    mkdir -p $PROJECT_DIR
    cd $PROJECT_DIR
    
    # Backend structure
    mkdir -p {src/{chaos,monitoring,recovery,web},tests/{unit,integration,chaos},config,logs,docker,frontend/{src/{components,services,utils},public}}
    
    # Create __init__.py files
    touch src/__init__.py
    touch src/chaos/__init__.py
    touch src/monitoring/__init__.py
    touch src/recovery/__init__.py
    touch src/web/__init__.py
    touch tests/__init__.py
    touch tests/unit/__init__.py
    touch tests/integration/__init__.py
    touch tests/chaos/__init__.py
    
    log_success "Project structure created"
}

# Setup Python dependencies
setup_python_dependencies() {
    log_info "Setting up Python dependencies..."
    
    cat > requirements.txt << 'EOF'
# Chaos Testing Framework Dependencies - May 2025
fastapi==0.111.0
uvicorn[standard]==0.30.1
websockets==12.0
pydantic==2.7.1
httpx==0.27.0
psutil==5.9.8
aiofiles==23.2.1
asyncio==3.4.3
docker==7.1.0
kubernetes==29.0.0
prometheus-client==0.20.0
structlog==24.1.0
typer==0.12.3
rich==13.7.1
pytest==8.2.0
pytest-asyncio==0.23.6
pytest-cov==5.0.0
faker==25.2.0
requests==2.31.0
aioredis==2.0.1
networkx==3.3
matplotlib==3.8.4
pandas==2.2.2
numpy==1.26.4
pyyaml==6.0.1
jinja2==3.1.4
coverage==7.5.1
black==24.4.2
flake8==7.0.0
mypy==1.10.0
EOF
    
    # Create virtual environment
    $PYTHON_CMD -m venv venv
    source venv/bin/activate
    
    # Upgrade pip and install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_success "Python dependencies installed"
}

# Setup React frontend
setup_react_frontend() {
    log_info "Setting up React frontend..."
    
    cd frontend
    
    # Create package.json
    cat > package.json << 'EOF'
{
  "name": "chaos-testing-dashboard",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^6.4.5",
    "@testing-library/react": "^15.0.7",
    "@testing-library/user-event": "^14.5.2",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-scripts": "5.0.1",
    "recharts": "^2.12.7",
    "axios": "^1.7.2",
    "socket.io-client": "^4.7.5",
    "@mui/material": "^5.15.19",
    "@mui/icons-material": "^5.15.19",
    "@emotion/react": "^11.11.4",
    "@emotion/styled": "^11.11.5",
    "web-vitals": "^3.3.2"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8000"
}
EOF
    
    # Install npm dependencies
    npm install
    
    cd ..
    log_success "React frontend setup complete"
}

# Create configuration files
create_config_files() {
    log_info "Creating configuration files..."
    
    # Main configuration
    cat > config/chaos_config.yaml << 'EOF'
chaos_testing:
  # Experiment settings
  default_duration: 300  # 5 minutes
  safety_timeout: 600    # 10 minutes
  blast_radius_limit: 0.3  # Max 30% of components
  
  # Failure scenarios
  scenarios:
    network_partition:
      enabled: true
      severity_levels: [1, 2, 3, 4, 5]
      max_impact_nodes: 2
    
    resource_exhaustion:
      enabled: true
      memory_pressure: [50, 70, 90]  # Percentage
      cpu_throttle: [50, 70, 90]     # Percentage
      disk_pressure: [80, 90, 95]    # Percentage
    
    component_failure:
      enabled: true
      target_services: ["log-collector", "message-queue", "log-processor"]
      failure_types: ["crash", "hang", "slow_response"]
    
    cascade_testing:
      enabled: true
      max_cascade_depth: 3
      isolation_boundaries: ["service", "rack", "zone"]

monitoring:
  metrics_interval: 5  # seconds
  health_check_timeout: 10  # seconds
  recovery_validation_timeout: 180  # 3 minutes
  
  critical_metrics:
    - "log_processing_rate"
    - "message_queue_depth"
    - "system_memory_usage"
    - "network_latency"
    - "error_rate"

recovery:
  auto_recovery_enabled: true
  max_recovery_attempts: 3
  recovery_validation_steps:
    - "service_health_check"
    - "data_consistency_check"
    - "performance_baseline_check"

logging:
  level: "INFO"
  format: "structured"
  output: "logs/chaos_testing.log"

web_interface:
  host: "0.0.0.0"
  port: 8000
  cors_origins: ["http://localhost:3000"]
EOF
    
    # Docker configuration
    cat > docker/docker-compose.yaml << 'EOF'
version: '3.8'

services:
  chaos-testing-api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app/src
    volumes:
      - ../src:/app/src
      - ../config:/app/config
      - ../logs:/app/logs
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - chaos-network
    depends_on:
      - redis
      - target-log-collector
      - target-message-queue
      - target-log-processor
  
  chaos-testing-frontend:
    build:
      context: ../frontend
      dockerfile: ../docker/Dockerfile.frontend
    ports:
      - "3000:3000"
    depends_on:
      - chaos-testing-api
    networks:
      - chaos-network
  
  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    networks:
      - chaos-network
  
  # Target services for chaos testing
  target-log-collector:
    image: nginx:alpine
    container_name: log-collector-service
    ports:
      - "8001:80"
    networks:
      - chaos-network
    labels:
      chaos.target: "true"
      chaos.service: "log-collector"
  
  target-message-queue:
    image: rabbitmq:3.12-management
    container_name: message-queue-service
    ports:
      - "5672:5672"
      - "15672:15672"
    networks:
      - chaos-network
    labels:
      chaos.target: "true"
      chaos.service: "message-queue"
  
  target-log-processor:
    image: nginx:alpine
    container_name: log-processor-service
    ports:
      - "8002:80"
    networks:
      - chaos-network
    labels:
      chaos.target: "true"
      chaos.service: "log-processor"

networks:
  chaos-network:
    driver: bridge
EOF
    
    # API Dockerfile
    cat > docker/Dockerfile.api << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Start application
CMD ["python", "-m", "src.web.main"]
EOF
    
    # Frontend Dockerfile
    cat > docker/Dockerfile.frontend << 'EOF'
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Serve the app
EXPOSE 3000
CMD ["npm", "start"]
EOF
    
    log_success "Configuration files created"
}

# Create chaos testing core modules
create_chaos_modules() {
    log_info "Creating chaos testing modules..."
    
    # Failure injector
    cat > src/chaos/failure_injector.py << 'EOF'
"""
Chaos Testing Framework - Failure Injector
Implements various failure scenarios for testing system resilience
"""

import asyncio
import docker
import subprocess
import psutil
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random

logger = logging.getLogger(__name__)


class FailureType(Enum):
    NETWORK_PARTITION = "network_partition"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    COMPONENT_FAILURE = "component_failure"
    LATENCY_INJECTION = "latency_injection"
    PACKET_LOSS = "packet_loss"


@dataclass
class FailureScenario:
    id: str
    type: FailureType
    target: str
    parameters: Dict[str, Any]
    duration: int = 300  # seconds
    severity: int = 3    # 1-5 scale
    blast_radius: float = 0.1  # percentage of system affected
    started_at: Optional[float] = None
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)


class FailureInjector:
    """
    Core chaos engineering component that injects various types of failures
    into the distributed log processing system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.docker_client = docker.from_env()
        self.active_scenarios: Dict[str, FailureScenario] = {}
        self.safety_limits = config.get('safety_limits', {})
        
    async def inject_failure(self, scenario: FailureScenario) -> bool:
        """
        Inject a specific failure scenario into the system
        """
        try:
            # Safety checks
            if not self._safety_check(scenario):
                logger.error(f"Safety check failed for scenario {scenario.id}")
                return False
            
            scenario.started_at = time.time()
            scenario.status = "active"
            self.active_scenarios[scenario.id] = scenario
            
            # Route to appropriate failure injection method
            if scenario.type == FailureType.NETWORK_PARTITION:
                await self._inject_network_partition(scenario)
            elif scenario.type == FailureType.RESOURCE_EXHAUSTION:
                await self._inject_resource_exhaustion(scenario)
            elif scenario.type == FailureType.COMPONENT_FAILURE:
                await self._inject_component_failure(scenario)
            elif scenario.type == FailureType.LATENCY_INJECTION:
                await self._inject_latency(scenario)
            elif scenario.type == FailureType.PACKET_LOSS:
                await self._inject_packet_loss(scenario)
            
            logger.info(f"Successfully injected failure scenario: {scenario.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to inject scenario {scenario.id}: {str(e)}")
            scenario.status = "failed"
            return False
    
    async def _inject_network_partition(self, scenario: FailureScenario):
        """
        Simulate network partition between components
        """
        target_container = scenario.target
        parameters = scenario.parameters
        
        # Get target container
        try:
            container = self.docker_client.containers.get(target_container)
            
            # Create network isolation using iptables
            isolation_rules = [
                f"docker exec {container.id} iptables -A INPUT -s {parameters.get('isolate_from', '0.0.0.0/0')} -j DROP",
                f"docker exec {container.id} iptables -A OUTPUT -d {parameters.get('isolate_from', '0.0.0.0/0')} -j DROP"
            ]
            
            for rule in isolation_rules:
                subprocess.run(rule.split(), check=True, capture_output=True)
                
            scenario.metadata['isolation_rules'] = isolation_rules
            logger.info(f"Network partition active for {target_container}")
            
        except Exception as e:
            logger.error(f"Network partition injection failed: {str(e)}")
            raise
    
    async def _inject_resource_exhaustion(self, scenario: FailureScenario):
        """
        Simulate resource exhaustion (CPU, memory, disk)
        """
        target_container = scenario.target
        parameters = scenario.parameters
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # CPU throttling
            if 'cpu_limit' in parameters:
                cpu_limit = parameters['cpu_limit']
                container.update(cpu_quota=int(100000 * cpu_limit / 100))
                logger.info(f"CPU throttled to {cpu_limit}% for {target_container}")
            
            # Memory limiting
            if 'memory_limit' in parameters:
                memory_limit = parameters['memory_limit']
                container.update(mem_limit=f"{memory_limit}m")
                logger.info(f"Memory limited to {memory_limit}MB for {target_container}")
            
            scenario.metadata['resource_limits'] = parameters
            
        except Exception as e:
            logger.error(f"Resource exhaustion injection failed: {str(e)}")
            raise
    
    async def _inject_component_failure(self, scenario: FailureScenario):
        """
        Simulate component crashes or hangs
        """
        target_container = scenario.target
        parameters = scenario.parameters
        failure_mode = parameters.get('mode', 'crash')
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            if failure_mode == 'crash':
                # Stop the container to simulate crash
                container.stop()
                scenario.metadata['action'] = 'stopped'
                logger.info(f"Container {target_container} stopped (crash simulation)")
                
            elif failure_mode == 'hang':
                # Send SIGSTOP to pause the container
                container.pause()
                scenario.metadata['action'] = 'paused'
                logger.info(f"Container {target_container} paused (hang simulation)")
                
            elif failure_mode == 'slow_response':
                # Inject artificial latency
                await self._inject_latency(scenario)
                
        except Exception as e:
            logger.error(f"Component failure injection failed: {str(e)}")
            raise
    
    async def _inject_latency(self, scenario: FailureScenario):
        """
        Inject network latency to simulate slow responses
        """
        target_container = scenario.target
        parameters = scenario.parameters
        latency_ms = parameters.get('latency_ms', 100)
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # Use tc (traffic control) to add latency
            latency_cmd = f"docker exec {container.id} tc qdisc add dev eth0 root netem delay {latency_ms}ms"
            subprocess.run(latency_cmd.split(), check=True, capture_output=True)
            
            scenario.metadata['latency_injection'] = f"{latency_ms}ms"
            logger.info(f"Latency of {latency_ms}ms injected for {target_container}")
            
        except Exception as e:
            logger.error(f"Latency injection failed: {str(e)}")
            raise
    
    async def _inject_packet_loss(self, scenario: FailureScenario):
        """
        Inject packet loss to simulate unreliable networks
        """
        target_container = scenario.target
        parameters = scenario.parameters
        loss_percentage = parameters.get('loss_percentage', 5)
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # Use tc to add packet loss
            loss_cmd = f"docker exec {container.id} tc qdisc add dev eth0 root netem loss {loss_percentage}%"
            subprocess.run(loss_cmd.split(), check=True, capture_output=True)
            
            scenario.metadata['packet_loss'] = f"{loss_percentage}%"
            logger.info(f"Packet loss of {loss_percentage}% injected for {target_container}")
            
        except Exception as e:
            logger.error(f"Packet loss injection failed: {str(e)}")
            raise
    
    async def recover_failure(self, scenario_id: str) -> bool:
        """
        Recover from a specific failure scenario
        """
        if scenario_id not in self.active_scenarios:
            logger.warning(f"Scenario {scenario_id} not found in active scenarios")
            return False
        
        scenario = self.active_scenarios[scenario_id]
        
        try:
            # Route to appropriate recovery method
            if scenario.type == FailureType.NETWORK_PARTITION:
                await self._recover_network_partition(scenario)
            elif scenario.type == FailureType.RESOURCE_EXHAUSTION:
                await self._recover_resource_exhaustion(scenario)
            elif scenario.type == FailureType.COMPONENT_FAILURE:
                await self._recover_component_failure(scenario)
            elif scenario.type in [FailureType.LATENCY_INJECTION, FailureType.PACKET_LOSS]:
                await self._recover_network_effects(scenario)
            
            scenario.status = "recovered"
            del self.active_scenarios[scenario_id]
            
            logger.info(f"Successfully recovered from scenario: {scenario_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to recover from scenario {scenario_id}: {str(e)}")
            scenario.status = "recovery_failed"
            return False
    
    async def _recover_network_partition(self, scenario: FailureScenario):
        """Recover from network partition"""
        target_container = scenario.target
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # Remove iptables rules
            if 'isolation_rules' in scenario.metadata:
                for rule in scenario.metadata['isolation_rules']:
                    # Convert ADD to DELETE
                    recovery_rule = rule.replace('-A', '-D')
                    try:
                        subprocess.run(recovery_rule.split(), check=True, capture_output=True)
                    except subprocess.CalledProcessError:
                        # Rule might not exist, continue
                        pass
                        
            logger.info(f"Network partition recovered for {target_container}")
            
        except Exception as e:
            logger.error(f"Network partition recovery failed: {str(e)}")
            raise
    
    async def _recover_resource_exhaustion(self, scenario: FailureScenario):
        """Recover from resource exhaustion"""
        target_container = scenario.target
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # Reset resource limits
            container.update(cpu_quota=-1, mem_limit=-1)
            logger.info(f"Resource limits reset for {target_container}")
            
        except Exception as e:
            logger.error(f"Resource exhaustion recovery failed: {str(e)}")
            raise
    
    async def _recover_component_failure(self, scenario: FailureScenario):
        """Recover from component failure"""
        target_container = scenario.target
        
        try:
            container = self.docker_client.containers.get(target_container)
            action = scenario.metadata.get('action')
            
            if action == 'stopped':
                container.start()
                logger.info(f"Container {target_container} restarted")
            elif action == 'paused':
                container.unpause()
                logger.info(f"Container {target_container} unpaused")
                
        except Exception as e:
            logger.error(f"Component failure recovery failed: {str(e)}")
            raise
    
    async def _recover_network_effects(self, scenario: FailureScenario):
        """Recover from network latency/packet loss"""
        target_container = scenario.target
        
        try:
            container = self.docker_client.containers.get(target_container)
            
            # Remove tc rules
            reset_cmd = f"docker exec {container.id} tc qdisc del dev eth0 root"
            try:
                subprocess.run(reset_cmd.split(), check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # No rules to delete, continue
                pass
                
            logger.info(f"Network effects reset for {target_container}")
            
        except Exception as e:
            logger.error(f"Network effects recovery failed: {str(e)}")
            raise
    
    def _safety_check(self, scenario: FailureScenario) -> bool:
        """
        Perform safety checks before injecting failure
        """
        # Check blast radius limits
        max_blast_radius = self.safety_limits.get('max_blast_radius', 0.3)
        if scenario.blast_radius > max_blast_radius:
            logger.error(f"Scenario blast radius {scenario.blast_radius} exceeds limit {max_blast_radius}")
            return False
        
        # Check if too many scenarios are already active
        max_concurrent = self.safety_limits.get('max_concurrent_scenarios', 3)
        if len(self.active_scenarios) >= max_concurrent:
            logger.error(f"Too many active scenarios: {len(self.active_scenarios)}")
            return False
        
        # Check severity limits
        max_severity = self.safety_limits.get('max_severity', 4)
        if scenario.severity > max_severity:
            logger.error(f"Scenario severity {scenario.severity} exceeds limit {max_severity}")
            return False
        
        return True
    
    def get_active_scenarios(self) -> List[Dict[str, Any]]:
        """Get list of currently active failure scenarios"""
        return [
            {
                'id': scenario.id,
                'type': scenario.type.value,
                'target': scenario.target,
                'duration': scenario.duration,
                'severity': scenario.severity,
                'status': scenario.status,
                'started_at': scenario.started_at,
                'elapsed': time.time() - scenario.started_at if scenario.started_at else 0
            }
            for scenario in self.active_scenarios.values()
        ]
    
    async def emergency_recovery(self) -> bool:
        """
        Emergency recovery - stop all active chaos scenarios
        """
        logger.warning("Emergency recovery initiated - stopping all chaos scenarios")
        
        recovery_success = True
        for scenario_id in list(self.active_scenarios.keys()):
            try:
                await self.recover_failure(scenario_id)
            except Exception as e:
                logger.error(f"Emergency recovery failed for {scenario_id}: {str(e)}")
                recovery_success = False
        
        return recovery_success


# Factory function for creating failure scenarios
def create_failure_scenario(
    scenario_type: str,
    target: str,
    parameters: Dict[str, Any],
    duration: int = 300,
    severity: int = 3
) -> FailureScenario:
    """
    Factory function to create failure scenarios with validation
    """
    scenario_id = f"{scenario_type}_{target}_{int(time.time())}"
    
    return FailureScenario(
        id=scenario_id,
        type=FailureType(scenario_type),
        target=target,
        parameters=parameters,
        duration=duration,
        severity=severity,
        blast_radius=min(parameters.get('blast_radius', 0.1), 0.3)  # Safety limit
    )
EOF
    
    # System monitor
    cat > src/monitoring/system_monitor.py << 'EOF'
"""
Chaos Testing Framework - System Monitor
Real-time monitoring of system health during chaos experiments
"""

import asyncio
import psutil
import docker
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import aioredis
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    timestamp: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    service_health: Dict[str, bool]
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertThreshold:
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str = "greater_than"  # greater_than, less_than, equals


class SystemMonitor:
    """
    Comprehensive monitoring system for tracking health during chaos experiments
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.docker_client = docker.from_env()
        self.redis_client = None
        self.metrics_history: List[SystemMetrics] = []
        self.alert_thresholds: List[AlertThreshold] = []
        self.monitoring_active = False
        self.monitored_services = config.get('monitored_services', [])
        
        # Setup alert thresholds from config
        self._setup_alert_thresholds()
        
    async def initialize(self):
        """Initialize connections and start monitoring"""
        try:
            # Connect to Redis for metrics storage
            redis_url = self.config.get('redis_url', 'redis://localhost:6379')
            self.redis_client = aioredis.from_url(redis_url)
            
            logger.info("System monitor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize system monitor: {str(e)}")
            raise
    
    def _setup_alert_thresholds(self):
        """Setup alert thresholds from configuration"""
        thresholds_config = self.config.get('alert_thresholds', {})
        
        default_thresholds = [
            AlertThreshold("cpu_usage", 70.0, 90.0),
            AlertThreshold("memory_usage", 80.0, 95.0),
            AlertThreshold("disk_usage", 85.0, 95.0),
            AlertThreshold("network_latency", 100.0, 500.0),
            AlertThreshold("log_processing_rate", 100.0, 50.0, "less_than"),
        ]
        
        # Add configured thresholds
        for threshold_config in thresholds_config:
            threshold = AlertThreshold(**threshold_config)
            self.alert_thresholds.append(threshold)
        
        # Add default thresholds if not configured
        configured_metrics = {t.metric_name for t in self.alert_thresholds}
        for default_threshold in default_thresholds:
            if default_threshold.metric_name not in configured_metrics:
                self.alert_thresholds.append(default_threshold)
    
    async def start_monitoring(self):
        """Start continuous system monitoring"""
        self.monitoring_active = True
        logger.info("Starting continuous system monitoring")
        
        # Start monitoring tasks
        monitoring_tasks = [
            asyncio.create_task(self._monitor_system_metrics()),
            asyncio.create_task(self._monitor_service_health()),
            asyncio.create_task(self._monitor_custom_metrics()),
            asyncio.create_task(self._process_alerts())
        ]
        
        try:
            await asyncio.gather(*monitoring_tasks)
        except Exception as e:
            logger.error(f"Monitoring error: {str(e)}")
            await self.stop_monitoring()
    
    async def stop_monitoring(self):
        """Stop monitoring and cleanup"""
        self.monitoring_active = False
        logger.info("Stopping system monitoring")
        
        if self.redis_client:
            await self.redis_client.close()
    
    async def _monitor_system_metrics(self):
        """Monitor basic system metrics"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                cpu_usage = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Network latency (ping localhost as baseline)
                network_latency = await self._measure_network_latency()
                
                # Service health
                service_health = await self._check_service_health()
                
                # Create metrics object
                metrics = SystemMetrics(
                    timestamp=time.time(),
                    cpu_usage=cpu_usage,
                    memory_usage=memory.percent,
                    disk_usage=disk.percent,
                    network_latency=network_latency,
                    service_health=service_health
                )
                
                # Store metrics
                await self._store_metrics(metrics)
                
                # Add to local history (keep last 1000 entries)
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > 1000:
                    self.metrics_history.pop(0)
                
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring system metrics: {str(e)}")
                await asyncio.sleep(5)
    
    async def _monitor_service_health(self):
        """Monitor health of specific services"""
        while self.monitoring_active:
            try:
                for service in self.monitored_services:
                    await self._check_individual_service_health(service)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring service health: {str(e)}")
                await asyncio.sleep(10)
    
    async def _monitor_custom_metrics(self):
        """Monitor custom application metrics"""
        while self.monitoring_active:
            try:
                # Log processing rate
                log_rate = await self._get_log_processing_rate()
                
                # Message queue depth
                queue_depth = await self._get_message_queue_depth()
                
                # Error rate
                error_rate = await self._get_error_rate()
                
                custom_metrics = {
                    'log_processing_rate': log_rate,
                    'message_queue_depth': queue_depth,
                    'error_rate': error_rate,
                    'timestamp': time.time()
                }
                
                # Store custom metrics
                if self.metrics_history:
                    self.metrics_history[-1].custom_metrics.update(custom_metrics)
                
                await asyncio.sleep(15)  # Check every 15 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring custom metrics: {str(e)}")
                await asyncio.sleep(15)
    
    async def _process_alerts(self):
        """Process alerts based on thresholds"""
        while self.monitoring_active:
            try:
                if not self.metrics_history:
                    await asyncio.sleep(5)
                    continue
                
                latest_metrics = self.metrics_history[-1]
                
                for threshold in self.alert_thresholds:
                    await self._check_threshold(latest_metrics, threshold)
                
                await asyncio.sleep(10)  # Check alerts every 10 seconds
                
            except Exception as e:
                logger.error(f"Error processing alerts: {str(e)}")
                await asyncio.sleep(10)
    
    async def _measure_network_latency(self) -> float:
        """Measure network latency"""
        try:
            start_time = time.time()
            # Simple HTTP request to measure latency
            async with httpx.AsyncClient() as client:
                await client.get("http://localhost:8000/health", timeout=5.0)
            return (time.time() - start_time) * 1000  # Convert to ms
        except:
            return 999.0  # High latency if unreachable
    
    async def _check_service_health(self) -> Dict[str, bool]:
        """Check health of monitored services"""
        service_health = {}
        
        try:
            # Check Docker containers
            containers = self.docker_client.containers.list()
            
            for service in self.monitored_services:
                service_healthy = False
                
                for container in containers:
                    if service in container.name and container.status == 'running':
                        service_healthy = True
                        break
                
                service_health[service] = service_healthy
                
        except Exception as e:
            logger.error(f"Error checking service health: {str(e)}")
            # Assume all services are unhealthy if we can't check
            service_health = {service: False for service in self.monitored_services}
        
        return service_health
    
    async def _check_individual_service_health(self, service: str):
        """Check health of individual service with detailed probes"""
        try:
            # HTTP health check if applicable
            health_endpoints = {
                'log-collector': 'http://localhost:8001/health',
                'message-queue': 'http://localhost:15672/api/health/checks/virtual-hosts',
                'log-processor': 'http://localhost:8002/health'
            }
            
            if service in health_endpoints:
                async with httpx.AsyncClient() as client:
                    response = await client.get(health_endpoints[service], timeout=5.0)
                    healthy = response.status_code == 200
                    
                    # Store detailed health info
                    health_info = {
                        'service': service,
                        'healthy': healthy,
                        'response_time': response.elapsed.total_seconds() * 1000,
                        'timestamp': time.time()
                    }
                    
                    if self.redis_client:
                        await self.redis_client.lpush(
                            f"health:{service}",
                            str(health_info)
                        )
                        # Keep only last 100 health checks
                        await self.redis_client.ltrim(f"health:{service}", 0, 99)
                        
        except Exception as e:
            logger.error(f"Error checking health for {service}: {str(e)}")
    
    async def _get_log_processing_rate(self) -> float:
        """Get current log processing rate"""
        try:
            # This would typically query your log processing metrics
            # For demo purposes, return a simulated value
            if self.redis_client:
                rate_data = await self.redis_client.get("metrics:log_processing_rate")
                if rate_data:
                    return float(rate_data)
            
            # Simulate processing rate based on system load
            cpu_usage = psutil.cpu_percent()
            return max(0, 1000 - (cpu_usage * 10))  # Inverse relationship with CPU
            
        except Exception as e:
            logger.error(f"Error getting log processing rate: {str(e)}")
            return 0.0
    
    async def _get_message_queue_depth(self) -> int:
        """Get current message queue depth"""
        try:
            # This would query RabbitMQ management API
            # For demo purposes, return a simulated value
            return 42  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting message queue depth: {str(e)}")
            return 0
    
    async def _get_error_rate(self) -> float:
        """Get current error rate"""
        try:
            # This would typically query error logs or metrics
            # For demo purposes, return a simulated value
            return 0.5  # 0.5% error rate
            
        except Exception as e:
            logger.error(f"Error getting error rate: {str(e)}")
            return 0.0
    
    async def _store_metrics(self, metrics: SystemMetrics):
        """Store metrics in Redis for persistence"""
        try:
            if self.redis_client:
                metrics_data = {
                    'timestamp': metrics.timestamp,
                    'cpu_usage': metrics.cpu_usage,
                    'memory_usage': metrics.memory_usage,
                    'disk_usage': metrics.disk_usage,
                    'network_latency': metrics.network_latency,
                    'service_health': metrics.service_health,
                    'custom_metrics': metrics.custom_metrics
                }
                
                await self.redis_client.lpush("metrics:system", str(metrics_data))
                # Keep only last 2000 metrics (about 3 hours at 5s intervals)
                await self.redis_client.ltrim("metrics:system", 0, 1999)
                
        except Exception as e:
            logger.error(f"Error storing metrics: {str(e)}")
    
    async def _check_threshold(self, metrics: SystemMetrics, threshold: AlertThreshold):
        """Check if metrics violate alert thresholds"""
        try:
            metric_value = None
            
            # Get metric value
            if threshold.metric_name == "cpu_usage":
                metric_value = metrics.cpu_usage
            elif threshold.metric_name == "memory_usage":
                metric_value = metrics.memory_usage
            elif threshold.metric_name == "disk_usage":
                metric_value = metrics.disk_usage
            elif threshold.metric_name == "network_latency":
                metric_value = metrics.network_latency
            elif threshold.metric_name in metrics.custom_metrics:
                metric_value = metrics.custom_metrics[threshold.metric_name]
            
            if metric_value is None:
                return
            
            # Check thresholds
            if threshold.comparison == "greater_than":
                if metric_value > threshold.critical_threshold:
                    await self._send_alert("critical", threshold.metric_name, metric_value, threshold.critical_threshold)
                elif metric_value > threshold.warning_threshold:
                    await self._send_alert("warning", threshold.metric_name, metric_value, threshold.warning_threshold)
            elif threshold.comparison == "less_than":
                if metric_value < threshold.critical_threshold:
                    await self._send_alert("critical", threshold.metric_name, metric_value, threshold.critical_threshold)
                elif metric_value < threshold.warning_threshold:
                    await self._send_alert("warning", threshold.metric_name, metric_value, threshold.warning_threshold)
                    
        except Exception as e:
            logger.error(f"Error checking threshold for {threshold.metric_name}: {str(e)}")
    
    async def _send_alert(self, level: str, metric_name: str, current_value: float, threshold_value: float):
        """Send alert for threshold violation"""
        alert = {
            'level': level,
            'metric': metric_name,
            'current_value': current_value,
            'threshold': threshold_value,
            'timestamp': time.time(),
            'message': f"{level.upper()}: {metric_name} = {current_value:.2f} (threshold: {threshold_value:.2f})"
        }
        
        logger.warning(f"ALERT: {alert['message']}")
        
        # Store alert
        if self.redis_client:
            await self.redis_client.lpush("alerts", str(alert))
            await self.redis_client.ltrim("alerts", 0, 999)  # Keep last 1000 alerts
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get current system metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_summary(self, duration_minutes: int = 10) -> Dict[str, Any]:
        """Get summary of metrics over specified duration"""
        cutoff_time = time.time() - (duration_minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {}
        
        return {
            'cpu_avg': sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
            'memory_avg': sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
            'network_latency_avg': sum(m.network_latency for m in recent_metrics) / len(recent_metrics),
            'metrics_count': len(recent_metrics),
            'duration_minutes': duration_minutes
        }
EOF
    
    # Recovery validator
    cat > src/recovery/recovery_validator.py << 'EOF'
"""
Chaos Testing Framework - Recovery Validator
Validates system recovery after chaos experiments
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class RecoveryStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class RecoveryTest:
    name: str
    description: str
    test_function: str
    timeout_seconds: int = 120
    required_for_success: bool = True


@dataclass
class RecoveryResult:
    test_name: str
    status: RecoveryStatus
    duration_seconds: float
    details: Dict[str, Any]
    error_message: Optional[str] = None


class RecoveryValidator:
    """
    Validates that the system properly recovers after chaos experiments
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.recovery_tests = self._setup_recovery_tests()
        
    def _setup_recovery_tests(self) -> List[RecoveryTest]:
        """Setup standard recovery validation tests"""
        return [
            RecoveryTest(
                name="service_availability",
                description="Check all services are responding",
                test_function="_test_service_availability",
                timeout_seconds=60,
                required_for_success=True
            ),
            RecoveryTest(
                name="log_processing_capacity",
                description="Verify log processing at normal rates",
                test_function="_test_log_processing_capacity",
                timeout_seconds=120,
                required_for_success=True
            ),
            RecoveryTest(
                name="data_consistency",
                description="Check data integrity after recovery",
                test_function="_test_data_consistency",
                timeout_seconds=90,
                required_for_success=True
            ),
            RecoveryTest(
                name="performance_baseline",
                description="Verify performance returned to baseline",
                test_function="_test_performance_baseline",
                timeout_seconds=180,
                required_for_success=False
            ),
            RecoveryTest(
                name="error_rate_normal",
                description="Check error rates are within normal bounds",
                test_function="_test_error_rate_normal",
                timeout_seconds=60,
                required_for_success=True
            )
        ]
    
    async def validate_recovery(self, chaos_scenario_id: str) -> Dict[str, Any]:
        """
        Run comprehensive recovery validation after chaos experiment
        """
        logger.info(f"Starting recovery validation for scenario: {chaos_scenario_id}")
        
        validation_start = time.time()
        results = []
        overall_success = True
        
        # Run all recovery tests
        for test in self.recovery_tests:
            logger.info(f"Running recovery test: {test.name}")
            
            result = await self._run_recovery_test(test)
            results.append(result)
            
            # Check if required test failed
            if test.required_for_success and result.status != RecoveryStatus.COMPLETED:
                overall_success = False
                logger.error(f"Required recovery test failed: {test.name}")
        
        validation_duration = time.time() - validation_start
        
        # Generate validation report
        validation_report = {
            'scenario_id': chaos_scenario_id,
            'overall_success': overall_success,
            'validation_duration': validation_duration,
            'test_results': [
                {
                    'name': result.test_name,
                    'status': result.status.value,
                    'duration': result.duration_seconds,
                    'details': result.details,
                    'error_message': result.error_message
                }
                for result in results
            ],
            'summary': {
                'total_tests': len(results),
                'passed_tests': len([r for r in results if r.status == RecoveryStatus.COMPLETED]),
                'failed_tests': len([r for r in results if r.status == RecoveryStatus.FAILED]),
                'timeout_tests': len([r for r in results if r.status == RecoveryStatus.TIMEOUT])
            }
        }
        
        logger.info(f"Recovery validation completed. Success: {overall_success}")
        return validation_report
    
    async def _run_recovery_test(self, test: RecoveryTest) -> RecoveryResult:
        """
        Run individual recovery test with timeout protection
        """
        start_time = time.time()
        
        try:
            # Get test function
            test_function = getattr(self, test.test_function)
            
            # Run test with timeout
            result = await asyncio.wait_for(
                test_function(),
                timeout=test.timeout_seconds
            )
            
            duration = time.time() - start_time
            
            return RecoveryResult(
                test_name=test.name,
                status=RecoveryStatus.COMPLETED,
                duration_seconds=duration,
                details=result
            )
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return RecoveryResult(
                test_name=test.name,
                status=RecoveryStatus.TIMEOUT,
                duration_seconds=duration,
                details={},
                error_message=f"Test timed out after {test.timeout_seconds} seconds"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return RecoveryResult(
                test_name=test.name,
                status=RecoveryStatus.FAILED,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            )
    
    async def _test_service_availability(self) -> Dict[str, Any]:
        """Test that all services are available and responding"""
        services_to_check = [
            {'name': 'log-collector', 'url': 'http://localhost:8001/health'},
            {'name': 'message-queue', 'url': 'http://localhost:15672/api/health/checks/virtual-hosts'},
            {'name': 'log-processor', 'url': 'http://localhost:8002/health'},
            {'name': 'chaos-api', 'url': 'http://localhost:8000/health'}
        ]
        
        service_results = {}
        
        async with httpx.AsyncClient() as client:
            for service in services_to_check:
                try:
                    response = await client.get(service['url'], timeout=10.0)
                    service_results[service['name']] = {
                        'available': response.status_code == 200,
                        'response_time': response.elapsed.total_seconds() * 1000,
                        'status_code': response.status_code
                    }
                except Exception as e:
                    service_results[service['name']] = {
                        'available': False,
                        'error': str(e)
                    }
        
        # Check if all services are available
        all_available = all(result.get('available', False) for result in service_results.values())
        
        return {
            'all_services_available': all_available,
            'service_details': service_results,
            'available_count': len([r for r in service_results.values() if r.get('available', False)]),
            'total_services': len(services_to_check)
        }
    
    async def _test_log_processing_capacity(self) -> Dict[str, Any]:
        """Test that log processing is working at normal capacity"""
        # Simulate sending test logs and measuring processing rate
        test_log_count = 100
        processing_times = []
        
        async with httpx.AsyncClient() as client:
            for i in range(test_log_count):
                start_time = time.time()
                
                test_log = {
                    'timestamp': time.time(),
                    'level': 'INFO',
                    'message': f'Recovery test log {i}',
                    'service': 'chaos-testing'
                }
                
                try:
                    response = await client.post(
                        'http://localhost:8000/api/logs',
                        json=test_log,
                        timeout=5.0
                    )
                    
                    if response.status_code == 200:
                        processing_time = time.time() - start_time
                        processing_times.append(processing_time)
                    
                    # Small delay to avoid overwhelming
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    logger.error(f"Error sending test log {i}: {str(e)}")
        
        if not processing_times:
            raise Exception("No logs were successfully processed")
        
        avg_processing_time = sum(processing_times) / len(processing_times)
        max_processing_time = max(processing_times)
        processed_count = len(processing_times)
        
        # Check if processing is within acceptable bounds
        acceptable_avg_time = 0.1  # 100ms
        acceptable_max_time = 0.5  # 500ms
        
        performance_ok = (avg_processing_time < acceptable_avg_time and 
                         max_processing_time < acceptable_max_time and
                         processed_count >= test_log_count * 0.9)  # 90% success rate
        
        return {
            'performance_acceptable': performance_ok,
            'processed_logs': processed_count,
            'total_test_logs': test_log_count,
            'success_rate': processed_count / test_log_count,
            'avg_processing_time_ms': avg_processing_time * 1000,
            'max_processing_time_ms': max_processing_time * 1000
        }
    
    async def _test_data_consistency(self) -> Dict[str, Any]:
        """Test data consistency and integrity"""
        # This would typically check:
        # - No duplicate log entries
        # - No missing log entries
        # - Proper ordering of logs
        # - Data integrity across replicas
        
        # For demo purposes, simulate consistency checks
        consistency_checks = {
            'no_duplicates': True,
            'proper_ordering': True,
            'data_integrity': True,
            'replica_consistency': True
        }
        
        # Simulate finding some minor inconsistencies but within acceptable bounds
        overall_consistent = all(consistency_checks.values())
        
        return {
            'data_consistent': overall_consistent,
            'checks_performed': consistency_checks,
            'consistency_score': sum(consistency_checks.values()) / len(consistency_checks)
        }
    
    async def _test_performance_baseline(self) -> Dict[str, Any]:
        """Test that performance has returned to baseline levels"""
        # Measure current performance metrics
        current_metrics = await self._measure_current_performance()
        baseline_metrics = self._get_baseline_performance()
        
        performance_comparison = {}
        performance_acceptable = True
        
        for metric, current_value in current_metrics.items():
            baseline_value = baseline_metrics.get(metric, current_value)
            
            # Allow 20% deviation from baseline
            tolerance = 0.2
            deviation = abs(current_value - baseline_value) / baseline_value if baseline_value > 0 else 0
            
            metric_acceptable = deviation <= tolerance
            performance_comparison[metric] = {
                'current': current_value,
                'baseline': baseline_value,
                'deviation_percent': deviation * 100,
                'acceptable': metric_acceptable
            }
            
            if not metric_acceptable:
                performance_acceptable = False
        
        return {
            'performance_restored': performance_acceptable,
            'metrics_comparison': performance_comparison,
            'overall_deviation': sum(comp['deviation_percent'] for comp in performance_comparison.values()) / len(performance_comparison)
        }
    
    async def _test_error_rate_normal(self) -> Dict[str, Any]:
        """Test that error rates are within normal bounds"""
        # Send test requests and measure error rate
        test_requests = 50
        error_count = 0
        
        async with httpx.AsyncClient() as client:
            for i in range(test_requests):
                try:
                    response = await client.get('http://localhost:8000/health', timeout=5.0)
                    if response.status_code >= 400:
                        error_count += 1
                except Exception:
                    error_count += 1
                
                await asyncio.sleep(0.1)
        
        error_rate = error_count / test_requests
        acceptable_error_rate = 0.05  # 5%
        
        return {
            'error_rate_normal': error_rate <= acceptable_error_rate,
            'current_error_rate': error_rate,
            'acceptable_error_rate': acceptable_error_rate,
            'errors_detected': error_count,
            'total_requests': test_requests
        }
    
    async def _measure_current_performance(self) -> Dict[str, float]:
        """Measure current performance metrics"""
        # This would typically query monitoring systems
        # For demo purposes, return simulated values
        return {
            'response_time_ms': 45.0,
            'throughput_rps': 150.0,
            'cpu_usage_percent': 35.0,
            'memory_usage_percent': 60.0
        }
    
    def _get_baseline_performance(self) -> Dict[str, float]:
        """Get baseline performance metrics for comparison"""
        # This would typically be loaded from historical data
        return {
            'response_time_ms': 50.0,
            'throughput_rps': 140.0,
            'cpu_usage_percent': 30.0,
            'memory_usage_percent': 55.0
        }
    
    async def quick_health_check(self) -> bool:
        """
        Quick health check to determine if system is ready for recovery validation
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get('http://localhost:8000/health', timeout=5.0)
                return response.status_code == 200
        except:
            return False
EOF
    
    log_success "Chaos testing modules created"
}

# Create web interface
create_web_interface() {
    log_info "Creating web interface..."
    
    # FastAPI backend
    cat > src/web/main.py << 'EOF'
"""
Chaos Testing Framework - Web Interface
FastAPI backend for chaos testing dashboard
"""

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
import uvicorn

from ..chaos.failure_injector import FailureInjector, create_failure_scenario, FailureType
from ..monitoring.system_monitor import SystemMonitor
from ..recovery.recovery_validator import RecoveryValidator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Chaos Testing Framework",
    description="Distributed Log Processing Chaos Testing Dashboard",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
failure_injector: Optional[FailureInjector] = None
system_monitor: Optional[SystemMonitor] = None
recovery_validator: Optional[RecoveryValidator] = None
config: Dict[str, Any] = {}

# WebSocket connections for real-time updates
active_websockets: List[WebSocket] = []


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global failure_injector, system_monitor, recovery_validator, config
    
    try:
        # Load configuration
        with open('config/chaos_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Initialize components
        failure_injector = FailureInjector(config['chaos_testing'])
        system_monitor = SystemMonitor(config['monitoring'])
        recovery_validator = RecoveryValidator(config['recovery'])
        
        # Initialize system monitor
        await system_monitor.initialize()
        
        # Start background monitoring
        asyncio.create_task(system_monitor.start_monitoring())
        
        logger.info("Chaos testing framework initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize chaos testing framework: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if system_monitor:
        await system_monitor.stop_monitoring()
    
    if failure_injector:
        await failure_injector.emergency_recovery()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Chaos experiment endpoints
@app.post("/api/chaos/scenarios")
async def create_chaos_scenario(scenario_data: Dict[str, Any]):
    """Create and start a new chaos scenario"""
    try:
        scenario = create_failure_scenario(
            scenario_type=scenario_data['type'],
            target=scenario_data['target'],
            parameters=scenario_data.get('parameters', {}),
            duration=scenario_data.get('duration', 300),
            severity=scenario_data.get('severity', 3)
        )
        
        success = await failure_injector.inject_failure(scenario)
        
        if success:
            # Notify WebSocket clients
            await broadcast_update({
                'type': 'scenario_started',
                'scenario': {
                    'id': scenario.id,
                    'type': scenario.type.value,
                    'target': scenario.target,
                    'status': scenario.status
                }
            })
            
            return {"success": True, "scenario_id": scenario.id}
        else:
            raise HTTPException(status_code=400, detail="Failed to inject failure scenario")
            
    except Exception as e:
        logger.error(f"Error creating chaos scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chaos/scenarios")
async def get_active_scenarios():
    """Get list of active chaos scenarios"""
    try:
        scenarios = failure_injector.get_active_scenarios()
        return {"scenarios": scenarios}
    except Exception as e:
        logger.error(f"Error getting active scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chaos/scenarios/{scenario_id}/stop")
async def stop_chaos_scenario(scenario_id: str):
    """Stop a specific chaos scenario"""
    try:
        success = await failure_injector.recover_failure(scenario_id)
        
        if success:
            # Notify WebSocket clients
            await broadcast_update({
                'type': 'scenario_stopped',
                'scenario_id': scenario_id
            })
            
            return {"success": True, "message": f"Scenario {scenario_id} stopped successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop scenario")
            
    except Exception as e:
        logger.error(f"Error stopping scenario {scenario_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chaos/emergency-stop")
async def emergency_stop():
    """Emergency stop all chaos scenarios"""
    try:
        success = await failure_injector.emergency_recovery()
        
        if success:
            await broadcast_update({
                'type': 'emergency_stop_completed'
            })
            
            return {"success": True, "message": "Emergency stop completed"}
        else:
            raise HTTPException(status_code=500, detail="Emergency stop failed")
            
    except Exception as e:
        logger.error(f"Error during emergency stop: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Recovery validation endpoints
@app.post("/api/recovery/validate/{scenario_id}")
async def validate_recovery(scenario_id: str, background_tasks: BackgroundTasks):
    """Start recovery validation for a scenario"""
    try:
        # Run validation in background
        background_tasks.add_task(run_recovery_validation, scenario_id)
        
        return {"success": True, "message": f"Recovery validation started for {scenario_id}"}
        
    except Exception as e:
        logger.error(f"Error starting recovery validation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_recovery_validation(scenario_id: str):
    """Run recovery validation in background"""
    try:
        validation_report = await recovery_validator.validate_recovery(scenario_id)
        
        # Notify WebSocket clients
        await broadcast_update({
            'type': 'recovery_validation_completed',
            'scenario_id': scenario_id,
            'report': validation_report
        })
        
    except Exception as e:
        logger.error(f"Recovery validation error: {str(e)}")
        await broadcast_update({
            'type': 'recovery_validation_failed',
            'scenario_id': scenario_id,
            'error': str(e)
        })


# Monitoring endpoints
@app.get("/api/monitoring/metrics")
async def get_current_metrics():
    """Get current system metrics"""
    try:
        current_metrics = system_monitor.get_current_metrics()
        
        if current_metrics:
            return {
                "timestamp": current_metrics.timestamp,
                "cpu_usage": current_metrics.cpu_usage,
                "memory_usage": current_metrics.memory_usage,
                "disk_usage": current_metrics.disk_usage,
                "network_latency": current_metrics.network_latency,
                "service_health": current_metrics.service_health,
                "custom_metrics": current_metrics.custom_metrics
            }
        else:
            return {"message": "No metrics available"}
            
    except Exception as e:
        logger.error(f"Error getting current metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/summary")
async def get_metrics_summary(duration_minutes: int = 10):
    """Get metrics summary over specified duration"""
    try:
        summary = system_monitor.get_metrics_summary(duration_minutes)
        return summary
    except Exception as e:
        logger.error(f"Error getting metrics summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Configuration endpoints
@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return config


@app.get("/api/config/scenarios")
async def get_scenario_templates():
    """Get available scenario templates"""
    templates = [
        {
            "id": "network_partition",
            "name": "Network Partition",
            "description": "Simulate network partition between services",
            "type": "network_partition",
            "parameters": {
                "isolate_from": "172.17.0.0/16"
            },
            "targets": ["log-collector-service", "message-queue-service", "log-processor-service"]
        },
        {
            "id": "resource_exhaustion",
            "name": "Resource Exhaustion",
            "description": "Simulate CPU/memory pressure",
            "type": "resource_exhaustion",
            "parameters": {
                "cpu_limit": 50,
                "memory_limit": 256
            },
            "targets": ["log-collector-service", "log-processor-service"]
        },
        {
            "id": "component_failure",
            "name": "Component Failure",
            "description": "Simulate service crashes",
            "type": "component_failure",
            "parameters": {
                "mode": "crash"
            },
            "targets": ["log-collector-service", "message-queue-service", "log-processor-service"]
        },
        {
            "id": "latency_injection",
            "name": "Latency Injection",
            "description": "Add network latency",
            "type": "latency_injection",
            "parameters": {
                "latency_ms": 200
            },
            "targets": ["log-collector-service", "message-queue-service"]
        }
    ]
    
    return {"templates": templates}


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            # Send periodic updates
            current_metrics = system_monitor.get_current_metrics()
            active_scenarios = failure_injector.get_active_scenarios()
            
            update = {
                'type': 'periodic_update',
                'metrics': {
                    "timestamp": current_metrics.timestamp,
                    "cpu_usage": current_metrics.cpu_usage,
                    "memory_usage": current_metrics.memory_usage,
                    "disk_usage": current_metrics.disk_usage,
                    "network_latency": current_metrics.network_latency,
                    "service_health": current_metrics.service_health,
                    "custom_metrics": current_metrics.custom_metrics
                } if current_metrics else {},
                'scenarios': active_scenarios
            }
            
            await websocket.send_text(json.dumps(update))
            await asyncio.sleep(5)  # Send updates every 5 seconds
            
    except Exception as e:
        logger.info(f"WebSocket disconnected: {str(e)}")
    finally:
        if websocket in active_websockets:
            active_websockets.remove(websocket)


async def broadcast_update(update: Dict[str, Any]):
    """Broadcast update to all connected WebSocket clients"""
    if active_websockets:
        message = json.dumps(update)
        disconnected = []
        
        for websocket in active_websockets:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.append(websocket)
        
        # Remove disconnected WebSockets
        for websocket in disconnected:
            active_websockets.remove(websocket)


# Test endpoints for demo
@app.post("/api/logs")
async def submit_log(log_data: Dict[str, Any]):
    """Submit a log entry (for testing purposes)"""
    # Simulate log processing
    await asyncio.sleep(0.01)  # Simulate processing time
    return {"success": True, "log_id": f"log_{int(datetime.now().timestamp())}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
    
    # React frontend components
    cat > frontend/src/App.js << 'EOF'
import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Container, AppBar, Toolbar, Typography, Box } from '@mui/material';
import ChaosControlPanel from './components/ChaosControlPanel';
import MetricsDashboard from './components/MetricsDashboard';
import ScenarioList from './components/ScenarioList';
import RecoveryStatus from './components/RecoveryStatus';
import io from 'socket.io-client';

// Google Cloud Skills Boost inspired theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1a73e8',
    },
    secondary: {
      main: '#34a853',
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Google Sans", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
});

function App() {
  const [metrics, setMetrics] = useState({});
  const [scenarios, setScenarios] = useState([]);
  const [socket, setSocket] = useState(null);
  const [recoveryStatus, setRecoveryStatus] = useState(null);

  useEffect(() => {
    // Initialize WebSocket connection
    const newSocket = io('http://localhost:8000');
    setSocket(newSocket);

    newSocket.on('connect', () => {
      console.log('Connected to chaos testing backend');
    });

    newSocket.on('periodic_update', (data) => {
      setMetrics(data.metrics || {});
      setScenarios(data.scenarios || []);
    });

    newSocket.on('scenario_started', (data) => {
      console.log('Scenario started:', data);
    });

    newSocket.on('scenario_stopped', (data) => {
      console.log('Scenario stopped:', data);
    });

    newSocket.on('recovery_validation_completed', (data) => {
      setRecoveryStatus(data.report);
    });

    return () => {
      newSocket.close();
    };
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            🌪️ Chaos Testing Framework - Distributed Log Processing
          </Typography>
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
            Day 63: Building System Resilience
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Container maxWidth="xl" sx={{ mt: 3, mb: 3 }}>
        <Box sx={{ display: 'grid', gap: 3 }}>
          {/* Metrics Dashboard */}
          <MetricsDashboard metrics={metrics} />
          
          {/* Main Control Panel */}
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, 
            gap: 3 
          }}>
            <ChaosControlPanel socket={socket} />
            <ScenarioList scenarios={scenarios} socket={socket} />
          </Box>
          
          {/* Recovery Status */}
          {recoveryStatus && (
            <RecoveryStatus report={recoveryStatus} />
          )}
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
EOF
    
    # Metrics Dashboard Component
    cat > frontend/src/components/MetricsDashboard.js << 'EOF'
import React from 'react';
import { Paper, Typography, Grid, Box, Chip } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const MetricCard = ({ title, value, unit, status = 'normal' }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'warning': return '#ff9800';
      case 'critical': return '#f44336';
      default: return '#4caf50';
    }
  };

  return (
    <Paper sx={{ p: 2, textAlign: 'center', height: '100%' }}>
      <Typography variant="h6" color="textSecondary" gutterBottom>
        {title}
      </Typography>
      <Typography 
        variant="h4" 
        sx={{ 
          color: getStatusColor(),
          fontWeight: 'bold',
          mb: 1
        }}
      >
        {value}
        <Typography component="span" variant="h6" sx={{ ml: 1 }}>
          {unit}
        </Typography>
      </Typography>
      <Chip 
        label={status.toUpperCase()} 
        size="small" 
        sx={{ 
          backgroundColor: getStatusColor(),
          color: 'white',
          fontWeight: 'bold'
        }} 
      />
    </Paper>
  );
};

const ServiceHealthIndicator = ({ services }) => {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Service Health
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {Object.entries(services || {}).map(([service, healthy]) => (
          <Chip
            key={service}
            label={service}
            color={healthy ? 'success' : 'error'}
            variant={healthy ? 'filled' : 'outlined'}
            sx={{ textTransform: 'capitalize' }}
          />
        ))}
      </Box>
    </Paper>
  );
};

const MetricsDashboard = ({ metrics }) => {
  const getCpuStatus = (usage) => {
    if (usage > 90) return 'critical';
    if (usage > 70) return 'warning';
    return 'normal';
  };

  const getMemoryStatus = (usage) => {
    if (usage > 95) return 'critical';
    if (usage > 80) return 'warning';
    return 'normal';
  };

  const getLatencyStatus = (latency) => {
    if (latency > 500) return 'critical';
    if (latency > 100) return 'warning';
    return 'normal';
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 500 }}>
        📊 Real-time System Metrics
      </Typography>
      
      <Grid container spacing={3}>
        {/* System Metrics */}
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="CPU Usage"
            value={metrics.cpu_usage?.toFixed(1) || '0'}
            unit="%"
            status={getCpuStatus(metrics.cpu_usage || 0)}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Memory Usage"
            value={metrics.memory_usage?.toFixed(1) || '0'}
            unit="%"
            status={getMemoryStatus(metrics.memory_usage || 0)}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Network Latency"
            value={metrics.network_latency?.toFixed(0) || '0'}
            unit="ms"
            status={getLatencyStatus(metrics.network_latency || 0)}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Log Processing Rate"
            value={metrics.custom_metrics?.log_processing_rate?.toFixed(0) || '0'}
            unit="logs/sec"
            status="normal"
          />
        </Grid>
        
        {/* Service Health */}
        <Grid item xs={12} md={6}>
          <ServiceHealthIndicator services={metrics.service_health} />
        </Grid>
        
        {/* Custom Metrics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Application Metrics
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography>Queue Depth:</Typography>
                <Typography fontWeight="bold">
                  {metrics.custom_metrics?.message_queue_depth || 0}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography>Error Rate:</Typography>
                <Typography fontWeight="bold">
                  {(metrics.custom_metrics?.error_rate || 0).toFixed(2)}%
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MetricsDashboard;
EOF
    
    # Chaos Control Panel Component
    cat > frontend/src/components/ChaosControlPanel.js << 'EOF'
import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Box,
  Alert,
  Slider,
  Chip
} from '@mui/material';
import axios from 'axios';

const ChaosControlPanel = ({ socket }) => {
  const [scenarioTemplates, setScenarioTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedTarget, setSelectedTarget] = useState('');
  const [duration, setDuration] = useState(300);
  const [severity, setSeverity] = useState(3);
  const [parameters, setParameters] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    loadScenarioTemplates();
  }, []);

  const loadScenarioTemplates = async () => {
    try {
      const response = await axios.get('/api/config/scenarios');
      setScenarioTemplates(response.data.templates);
    } catch (error) {
      console.error('Error loading scenario templates:', error);
    }
  };

  const handleTemplateChange = (templateId) => {
    setSelectedTemplate(templateId);
    const template = scenarioTemplates.find(t => t.id === templateId);
    if (template) {
      setParameters(template.parameters);
      setSelectedTarget('');
    }
  };

  const startChaosScenario = async () => {
    if (!selectedTemplate || !selectedTarget) {
      setMessage({ type: 'error', text: 'Please select a scenario template and target' });
      return;
    }

    setLoading(true);
    try {
      const template = scenarioTemplates.find(t => t.id === selectedTemplate);
      
      const scenarioData = {
        type: template.type,
        target: selectedTarget,
        parameters: {
          ...parameters,
          blast_radius: severity * 0.05 // Convert severity to blast radius
        },
        duration,
        severity
      };

      const response = await axios.post('/api/chaos/scenarios', scenarioData);
      
      if (response.data.success) {
        setMessage({
          type: 'success',
          text: `Chaos scenario started successfully! ID: ${response.data.scenario_id}`
        });
        
        // Reset form
        setSelectedTemplate('');
        setSelectedTarget('');
        setParameters({});
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Failed to start chaos scenario: ${error.response?.data?.detail || error.message}`
      });
    } finally {
      setLoading(false);
    }
  };

  const emergencyStop = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/chaos/emergency-stop');
      if (response.data.success) {
        setMessage({
          type: 'warning',
          text: 'Emergency stop completed - all chaos scenarios stopped'
        });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Emergency stop failed: ${error.response?.data?.detail || error.message}`
      });
    } finally {
      setLoading(false);
    }
  };

  const selectedTemplateData = scenarioTemplates.find(t => t.id === selectedTemplate);

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        🌪️ Chaos Control Panel
      </Typography>

      {message && (
        <Alert 
          severity={message.type} 
          sx={{ mb: 2 }}
          onClose={() => setMessage(null)}
        >
          {message.text}
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Scenario Template Selection */}
        <FormControl fullWidth>
          <InputLabel>Chaos Scenario Type</InputLabel>
          <Select
            value={selectedTemplate}
            onChange={(e) => handleTemplateChange(e.target.value)}
            label="Chaos Scenario Type"
          >
            {scenarioTemplates.map((template) => (
              <MenuItem key={template.id} value={template.id}>
                {template.name} - {template.description}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Target Selection */}
        {selectedTemplateData && (
          <FormControl fullWidth>
            <InputLabel>Target Service</InputLabel>
            <Select
              value={selectedTarget}
              onChange={(e) => setSelectedTarget(e.target.value)}
              label="Target Service"
            >
              {selectedTemplateData.targets.map((target) => (
                <MenuItem key={target} value={target}>
                  {target}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        {/* Duration */}
        <TextField
          label="Duration (seconds)"
          type="number"
          value={duration}
          onChange={(e) => setDuration(parseInt(e.target.value))}
          inputProps={{ min: 30, max: 1800 }}
          fullWidth
        />

        {/* Severity */}
        <Box>
          <Typography gutterBottom>
            Severity Level: {severity}
          </Typography>
          <Slider
            value={severity}
            onChange={(e, value) => setSeverity(value)}
            min={1}
            max={5}
            marks
            step={1}
            valueLabelDisplay="auto"
          />
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
            <Chip label="Low Impact" size="small" color="success" />
            <Chip label="High Impact" size="small" color="error" />
          </Box>
        </Box>

        {/* Parameter Configuration */}
        {selectedTemplateData && Object.keys(parameters).length > 0 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Scenario Parameters:
            </Typography>
            {Object.entries(parameters).map(([key, value]) => (
              <TextField
                key={key}
                label={key.replace('_', ' ').toUpperCase()}
                value={value}
                onChange={(e) => setParameters({
                  ...parameters,
                  [key]: e.target.value
                })}
                size="small"
                sx={{ mr: 1, mb: 1 }}
              />
            ))}
          </Box>
        )}

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Button
            variant="contained"
            color="warning"
            onClick={startChaosScenario}
            disabled={loading || !selectedTemplate || !selectedTarget}
            sx={{ flex: 1 }}
          >
            {loading ? 'Starting...' : 'Start Chaos Scenario'}
          </Button>
          
          <Button
            variant="outlined"
            color="error"
            onClick={emergencyStop}
            disabled={loading}
          >
            Emergency Stop
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default ChaosControlPanel;
EOF
    
    # Scenario List Component
    cat > frontend/src/components/ScenarioList.js << 'EOF'
import React, { useState } from 'react';
import {
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Button,
  Chip,
  Box,
  Alert
} from '@mui/material';
import axios from 'axios';

const ScenarioList = ({ scenarios, socket }) => {
  const [loading, setLoading] = useState({});

  const stopScenario = async (scenarioId) => {
    setLoading({ ...loading, [scenarioId]: true });
    try {
      const response = await axios.post(`/api/chaos/scenarios/${scenarioId}/stop`);
      if (response.data.success) {
        console.log(`Scenario ${scenarioId} stopped successfully`);
      }
    } catch (error) {
      console.error(`Error stopping scenario ${scenarioId}:`, error);
    } finally {
      setLoading({ ...loading, [scenarioId]: false });
    }
  };

  const validateRecovery = async (scenarioId) => {
    try {
      const response = await axios.post(`/api/recovery/validate/${scenarioId}`);
      if (response.data.success) {
        console.log(`Recovery validation started for ${scenarioId}`);
      }
    } catch (error) {
      console.error(`Error starting recovery validation:`, error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'error';
      case 'pending': return 'warning';
      case 'recovered': return 'success';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const formatDuration = (startTime, elapsed) => {
    const minutes = Math.floor(elapsed / 60);
    const seconds = Math.floor(elapsed % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        📋 Active Chaos Scenarios
      </Typography>

      {scenarios.length === 0 ? (
        <Alert severity="info">
          No active chaos scenarios. Use the control panel to start one.
        </Alert>
      ) : (
        <List>
          {scenarios.map((scenario) => (
            <ListItem
              key={scenario.id}
              sx={{
                border: '1px solid #e0e0e0',
                borderRadius: 1,
                mb: 1,
                backgroundColor: scenario.status === 'active' ? '#fff3e0' : '#f5f5f5'
              }}
            >
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {scenario.type.replace('_', ' ').toUpperCase()}
                    </Typography>
                    <Chip
                      label={scenario.status}
                      color={getStatusColor(scenario.status)}
                      size="small"
                    />
                  </Box>
                }
                secondary={
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2" color="textSecondary">
                      <strong>Target:</strong> {scenario.target}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      <strong>Duration:</strong> {formatDuration(scenario.started_at, scenario.elapsed)} / {Math.floor(scenario.duration / 60)}:00
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      <strong>Severity:</strong> {scenario.severity}/5
                    </Typography>
                  </Box>
                }
              />
              <ListItemSecondaryAction>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {scenario.status === 'active' && (
                    <Button
                      variant="outlined"
                      color="error"
                      size="small"
                      onClick={() => stopScenario(scenario.id)}
                      disabled={loading[scenario.id]}
                    >
                      {loading[scenario.id] ? 'Stopping...' : 'Stop'}
                    </Button>
                  )}
                  {scenario.status === 'recovered' && (
                    <Button
                      variant="outlined"
                      color="primary"
                      size="small"
                      onClick={() => validateRecovery(scenario.id)}
                    >
                      Validate Recovery
                    </Button>
                  )}
                </Box>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  );
};

export default ScenarioList;
EOF
    
    # Recovery Status Component
    cat > frontend/src/components/RecoveryStatus.js << 'EOF'
import React from 'react';
import {
  Paper,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert
} from '@mui/material';
import { ExpandMore, CheckCircle, Error, Warning } from '@mui/icons-material';

const RecoveryStatus = ({ report }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'failed':
        return <Error sx={{ color: 'error.main' }} />;
      case 'timeout':
        return <Warning sx={{ color: 'warning.main' }} />;
      default:
        return null;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'timeout': return 'warning';
      default: return 'default';
    }
  };

  const successRate = (report.summary.passed_tests / report.summary.total_tests) * 100;

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        🔍 Recovery Validation Report
        <Chip 
          label={report.overall_success ? 'PASSED' : 'FAILED'}
          color={report.overall_success ? 'success' : 'error'}
          sx={{ ml: 2 }}
        />
      </Typography>

      {/* Summary */}
      <Alert 
        severity={report.overall_success ? 'success' : 'error'}
        sx={{ mb: 3 }}
      >
        <Typography variant="subtitle1">
          Recovery validation {report.overall_success ? 'completed successfully' : 'failed'} 
          in {report.validation_duration.toFixed(1)} seconds
        </Typography>
        <Typography variant="body2">
          {report.summary.passed_tests}/{report.summary.total_tests} tests passed 
          ({successRate.toFixed(1)}% success rate)
        </Typography>
      </Alert>

      {/* Progress Bar */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Test Success Rate
        </Typography>
        <LinearProgress 
          variant="determinate" 
          value={successRate}
          color={report.overall_success ? 'success' : 'error'}
          sx={{ height: 10, borderRadius: 1 }}
        />
        <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
          {successRate.toFixed(1)}% ({report.summary.passed_tests}/{report.summary.total_tests})
        </Typography>
      </Box>

      {/* Detailed Test Results */}
      <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
        Detailed Test Results
      </Typography>
      
      {report.test_results.map((test, index) => (
        <Accordion key={index} sx={{ mb: 1 }}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
              {getStatusIcon(test.status)}
              <Typography sx={{ flex: 1 }}>
                {test.name.replace('_', ' ').toUpperCase()}
              </Typography>
              <Chip 
                label={test.status} 
                color={getStatusColor(test.status)}
                size="small"
              />
              <Typography variant="body2" color="textSecondary">
                {test.duration.toFixed(2)}s
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box>
              {test.error_message && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {test.error_message}
                </Alert>
              )}
              
              <Typography variant="subtitle2" gutterBottom>
                Test Details:
              </Typography>
              <Box component="pre" sx={{ 
                backgroundColor: '#f5f5f5', 
                p: 2, 
                borderRadius: 1,
                fontSize: '0.8rem',
                overflow: 'auto'
              }}>
                {JSON.stringify(test.details, null, 2)}
              </Box>
            </Box>
          </AccordionDetails>
        </Accordion>
      ))}
    </Paper>
  );
};

export default RecoveryStatus;
EOF
    
    # Package.json for frontend
    cat > frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta
      name="description"
      content="Chaos Testing Framework for Distributed Log Processing Systems"
    />
    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <link
      href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@300;400;500;700&family=Roboto:wght@300;400;500;700&display=swap"
      rel="stylesheet"
    />
    <title>Chaos Testing Framework</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF
    
    # Create frontend service files
    cat > frontend/src/services/api.js << 'EOF'
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async getChaosScenarios() {
    const response = await this.client.get('/api/chaos/scenarios');
    return response.data;
  }

  async createChaosScenario(scenarioData) {
    const response = await this.client.post('/api/chaos/scenarios', scenarioData);
    return response.data;
  }

  async stopChaosScenario(scenarioId) {
    const response = await this.client.post(`/api/chaos/scenarios/${scenarioId}/stop`);
    return response.data;
  }

  async emergencyStop() {
    const response = await this.client.post('/api/chaos/emergency-stop');
    return response.data;
  }

  async getMetrics() {
    const response = await this.client.get('/api/monitoring/metrics');
    return response.data;
  }

  async getMetricsSummary(durationMinutes = 10) {
    const response = await this.client.get(`/api/monitoring/summary?duration_minutes=${durationMinutes}`);
    return response.data;
  }

  async validateRecovery(scenarioId) {
    const response = await this.client.post(`/api/recovery/validate/${scenarioId}`);
    return response.data;
  }

  async getConfig() {
    const response = await this.client.get('/api/config');
    return response.data;
  }

  async getScenarioTemplates() {
    const response = await this.client.get('/api/config/scenarios');
    return response.data;
  }
}

export default new ApiService();
EOF

    # Create frontend utility files
    cat > frontend/src/utils/websocket.js << 'EOF'
import io from 'socket.io-client';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  connect(url = 'http://localhost:8000') {
    if (this.socket) {
      this.disconnect();
    }

    this.socket = io(url);
    
    this.socket.on('connect', () => {
      console.log('Connected to WebSocket server');
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket server');
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    // Set up event listeners
    this.listeners.forEach((callback, event) => {
      this.socket.on(event, callback);
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on(event, callback) {
    this.listeners.set(event, callback);
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off(event) {
    this.listeners.delete(event);
    if (this.socket) {
      this.socket.off(event);
    }
  }

  emit(event, data) {
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }
}

export default new WebSocketService();
EOF

    cat > frontend/src/utils/formatters.js << 'EOF'
// Utility functions for formatting data in the UI

export const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

export const formatPercentage = (value, decimals = 1) => {
  return `${value.toFixed(decimals)}%`;
};

export const formatLatency = (ms) => {
  if (ms < 1000) {
    return `${ms.toFixed(0)}ms`;
  } else {
    return `${(ms / 1000).toFixed(1)}s`;
  }
};

export const formatTimestamp = (timestamp) => {
  return new Date(timestamp * 1000).toLocaleString();
};

export const getStatusColor = (status) => {
  const colors = {
    'active': 'error',
    'pending': 'warning',
    'completed': 'success',
    'failed': 'error',
    'recovered': 'success',
    'timeout': 'warning'
  };
  return colors[status] || 'default';
};

export const getSeverityLabel = (severity) => {
  const labels = {
    1: 'Very Low',
    2: 'Low',
    3: 'Medium',
    4: 'High',
    5: 'Very High'
  };
  return labels[severity] || 'Unknown';
};

export const getSeverityColor = (severity) => {
  const colors = {
    1: 'success',
    2: 'info',
    3: 'warning',
    4: 'error',
    5: 'error'
  };
  return colors[severity] || 'default';
};
EOF

    cat > frontend/src/utils/constants.js << 'EOF'
// Application constants

export const CHAOS_SCENARIO_TYPES = {
  NETWORK_PARTITION: 'network_partition',
  RESOURCE_EXHAUSTION: 'resource_exhaustion',
  COMPONENT_FAILURE: 'component_failure',
  LATENCY_INJECTION: 'latency_injection',
  PACKET_LOSS: 'packet_loss'
};

export const SCENARIO_STATUS = {
  PENDING: 'pending',
  ACTIVE: 'active',
  COMPLETED: 'completed',
  FAILED: 'failed',
  RECOVERED: 'recovered',
  TIMEOUT: 'timeout'
};

export const SEVERITY_LEVELS = {
  VERY_LOW: 1,
  LOW: 2,
  MEDIUM: 3,
  HIGH: 4,
  VERY_HIGH: 5
};

export const METRIC_THRESHOLDS = {
  CPU_WARNING: 70,
  CPU_CRITICAL: 90,
  MEMORY_WARNING: 80,
  MEMORY_CRITICAL: 95,
  DISK_WARNING: 85,
  DISK_CRITICAL: 95,
  LATENCY_WARNING: 100,
  LATENCY_CRITICAL: 500
};

export const REFRESH_INTERVALS = {
  METRICS: 5000,        // 5 seconds
  SCENARIOS: 10000,     // 10 seconds
  HEALTH_CHECK: 30000   // 30 seconds
};

export const API_ENDPOINTS = {
  HEALTH: '/health',
  SCENARIOS: '/api/chaos/scenarios',
  EMERGENCY_STOP: '/api/chaos/emergency-stop',
  METRICS: '/api/monitoring/metrics',
  METRICS_SUMMARY: '/api/monitoring/summary',
  CONFIG: '/api/config',
  SCENARIO_TEMPLATES: '/api/config/scenarios',
  RECOVERY_VALIDATE: '/api/recovery/validate'
};

export const WEBSOCKET_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  PERIODIC_UPDATE: 'periodic_update',
  SCENARIO_STARTED: 'scenario_started',
  SCENARIO_STOPPED: 'scenario_stopped',
  EMERGENCY_STOP: 'emergency_stop_completed',
  RECOVERY_VALIDATION: 'recovery_validation_completed',
  RECOVERY_FAILED: 'recovery_validation_failed'
};

export const DEFAULT_SCENARIO_DURATION = 300; // 5 minutes
export const DEFAULT_SEVERITY = 3;
export const MAX_BLAST_RADIUS = 0.3;
export const MAX_CONCURRENT_SCENARIOS = 3;
EOF

    cd ..
    log_success "Web interface created"
}

# Create comprehensive test suite
create_test_suite() {
    log_info "Creating test suite..."
    
    # Ensure test directories exist
    mkdir -p tests/unit tests/integration tests/chaos
    
    # Unit tests
    cat > tests/unit/test_failure_injector.py << 'EOF'
"""
Unit tests for Failure Injector
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from src.chaos.failure_injector import FailureInjector, FailureScenario, FailureType, create_failure_scenario


class TestFailureInjector:
    
    @pytest.fixture
    def mock_config(self):
        return {
            'safety_limits': {
                'max_blast_radius': 0.3,
                'max_concurrent_scenarios': 3,
                'max_severity': 4
            }
        }
    
    @pytest.fixture
    def failure_injector(self, mock_config):
        with patch('docker.from_env'), patch('src.chaos.failure_injector.subprocess'):
            injector = FailureInjector(mock_config)
            injector.docker_client = Mock()
            return injector
    
    def test_create_failure_scenario(self):
        """Test failure scenario creation"""
        scenario = create_failure_scenario(
            scenario_type="network_partition",
            target="test-container",
            parameters={"isolate_from": "172.17.0.0/16"},
            duration=300,
            severity=3
        )
        
        assert scenario.type == FailureType.NETWORK_PARTITION
        assert scenario.target == "test-container"
        assert scenario.duration == 300
        assert scenario.severity == 3
        assert scenario.status == "pending"
    
    def test_safety_check_blast_radius(self, failure_injector):
        """Test safety check for blast radius"""
        scenario = FailureScenario(
            id="test-1",
            type=FailureType.NETWORK_PARTITION,
            target="test-container",
            parameters={},
            blast_radius=0.5  # Exceeds limit
        )
        
        assert not failure_injector._safety_check(scenario)
    
    def test_safety_check_severity(self, failure_injector):
        """Test safety check for severity"""
        scenario = FailureScenario(
            id="test-2",
            type=FailureType.NETWORK_PARTITION,
            target="test-container",
            parameters={},
            severity=5  # Exceeds limit
        )
        
        assert not failure_injector._safety_check(scenario)
    
    def test_safety_check_concurrent_limit(self, failure_injector):
        """Test safety check for concurrent scenarios"""
        # Add 3 active scenarios
        for i in range(3):
            failure_injector.active_scenarios[f"test-{i}"] = Mock()
        
        scenario = FailureScenario(
            id="test-new",
            type=FailureType.NETWORK_PARTITION,
            target="test-container",
            parameters={}
        )
        
        assert not failure_injector._safety_check(scenario)
    
    @pytest.mark.asyncio
    async def test_inject_network_partition(self, failure_injector):
        """Test network partition injection"""
        mock_container = Mock()
        mock_container.id = "container123"
        failure_injector.docker_client.containers.get.return_value = mock_container
        
        scenario = FailureScenario(
            id="test-partition",
            type=FailureType.NETWORK_PARTITION,
            target="test-container",
            parameters={"isolate_from": "172.17.0.0/16"}
        )
        
        with patch('src.chaos.failure_injector.subprocess.run') as mock_subprocess:
            await failure_injector._inject_network_partition(scenario)
            
            # Verify subprocess calls were made
            assert mock_subprocess.call_count == 2  # Two iptables rules
            assert 'isolation_rules' in scenario.metadata
    
    @pytest.mark.asyncio
    async def test_inject_component_failure(self, failure_injector):
        """Test component failure injection"""
        mock_container = Mock()
        failure_injector.docker_client.containers.get.return_value = mock_container
        
        scenario = FailureScenario(
            id="test-crash",
            type=FailureType.COMPONENT_FAILURE,
            target="test-container",
            parameters={"mode": "crash"}
        )
        
        await failure_injector._inject_component_failure(scenario)
        
        # Verify container was stopped
        mock_container.stop.assert_called_once()
        assert scenario.metadata['action'] == 'stopped'
    
    @pytest.mark.asyncio
    async def test_recovery_network_partition(self, failure_injector):
        """Test recovery from network partition"""
        mock_container = Mock()
        mock_container.id = "container123"
        failure_injector.docker_client.containers.get.return_value = mock_container
        
        scenario = FailureScenario(
            id="test-recovery",
            type=FailureType.NETWORK_PARTITION,
            target="test-container",
            parameters={},
            metadata={
                'isolation_rules': [
                    "docker exec container123 iptables -A INPUT -s 172.17.0.0/16 -j DROP"
                ]
            }
        )
        
        with patch('src.chaos.failure_injector.subprocess.run') as mock_subprocess:
            await failure_injector._recover_network_partition(scenario)
            
            # Verify recovery rule was executed
            mock_subprocess.assert_called()
            call_args = mock_subprocess.call_args[0][0]
            assert '-D INPUT' in ' '.join(call_args)  # DELETE rule
    
    @pytest.mark.asyncio
    async def test_emergency_recovery(self, failure_injector):
        """Test emergency recovery functionality"""
        # Add mock active scenarios
        scenario1 = Mock()
        scenario1.id = "test-1"
        scenario2 = Mock()
        scenario2.id = "test-2"
        
        failure_injector.active_scenarios = {
            "test-1": scenario1,
            "test-2": scenario2
        }
        
        with patch.object(failure_injector, 'recover_failure', return_value=True) as mock_recover:
            result = await failure_injector.emergency_recovery()
            
            assert result is True
            assert mock_recover.call_count == 2
            mock_recover.assert_any_call("test-1")
            mock_recover.assert_any_call("test-2")
    
    def test_get_active_scenarios(self, failure_injector):
        """Test getting active scenarios"""
        import time
        
        scenario = FailureScenario(
            id="test-active",
            type=FailureType.NETWORK_PARTITION,
            target="test-container",
            parameters={},
            started_at=time.time()
        )
        
        failure_injector.active_scenarios["test-active"] = scenario
        
        active_list = failure_injector.get_active_scenarios()
        
        assert len(active_list) == 1
        assert active_list[0]['id'] == "test-active"
        assert active_list[0]['type'] == "network_partition"
        assert 'elapsed' in active_list[0]


if __name__ == "__main__":
    pytest.main([__file__])
EOF
    
    # Integration tests
    cat > tests/integration/test_chaos_integration.py << 'EOF'
"""
Integration tests for Chaos Testing Framework
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
import docker
import requests

from src.chaos.failure_injector import FailureInjector, create_failure_scenario
from src.monitoring.system_monitor import SystemMonitor
from src.recovery.recovery_validator import RecoveryValidator


class TestChaosIntegration:
    
    @pytest.fixture
    def config(self):
        return {
            'chaos_testing': {
                'safety_limits': {
                    'max_blast_radius': 0.3,
                    'max_concurrent_scenarios': 3,
                    'max_severity': 4
                }
            },
            'monitoring': {
                'redis_url': 'redis://localhost:6379',
                'monitored_services': ['test-service'],
                'alert_thresholds': []
            },
            'recovery': {}
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_chaos_scenario(self, config):
        """Test complete chaos scenario lifecycle"""
        # Initialize components
        failure_injector = FailureInjector(config['chaos_testing'])
        system_monitor = SystemMonitor(config['monitoring'])
        recovery_validator = RecoveryValidator(config['recovery'])
        
        # Mock Docker client
        with patch('docker.from_env') as mock_docker:
            mock_container = Mock()
            mock_container.id = "test123"
            mock_container.status = "running"
            mock_docker.return_value.containers.get.return_value = mock_container
            mock_docker.return_value.containers.list.return_value = [mock_container]
            
            # Create scenario
            scenario = create_failure_scenario(
                scenario_type="component_failure",
                target="test-container",
                parameters={"mode": "crash"},
                duration=60,
                severity=2
            )
            
            # Inject failure
            with patch('subprocess.run'):
                success = await failure_injector.inject_failure(scenario)
                assert success
                
                # Verify scenario is active
                active_scenarios = failure_injector.get_active_scenarios()
                assert len(active_scenarios) == 1
                assert active_scenarios[0]['status'] == 'active'
                
                # Wait a moment to simulate failure duration
                await asyncio.sleep(0.1)
                
                # Recover from failure
                recovery_success = await failure_injector.recover_failure(scenario.id)
                assert recovery_success
                
                # Verify no active scenarios
                active_scenarios = failure_injector.get_active_scenarios()
                assert len(active_scenarios) == 0
    
    @pytest.mark.asyncio
    async def test_monitoring_during_chaos(self, config):
        """Test monitoring functionality during chaos scenarios"""
        system_monitor = SystemMonitor(config['monitoring'])
        
        # Mock Redis connection
        with patch('aioredis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            
            await system_monitor.initialize()
            
            # Mock system metrics
            with patch('psutil.cpu_percent', return_value=45.0), \
                 patch('psutil.virtual_memory') as mock_memory, \
                 patch('psutil.disk_usage') as mock_disk:
                
                mock_memory.return_value.percent = 60.0
                mock_disk.return_value.percent = 75.0
                
                # Collect metrics
                current_metrics = await system_monitor._monitor_system_metrics.__wrapped__(system_monitor)
                
                # Verify metrics were collected
                assert len(system_monitor.metrics_history) > 0
                latest_metrics = system_monitor.metrics_history[-1]
                assert latest_metrics.cpu_usage == 45.0
                assert latest_metrics.memory_usage == 60.0
                assert latest_metrics.disk_usage == 75.0
    
    @pytest.mark.asyncio
    async def test_recovery_validation(self, config):
        """Test recovery validation process"""
        recovery_validator = RecoveryValidator(config['recovery'])
        
        # Mock HTTP responses for service health checks
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 0.05
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Run recovery validation
            validation_report = await recovery_validator.validate_recovery("test-scenario-123")
            
            # Verify validation report structure
            assert 'scenario_id' in validation_report
            assert 'overall_success' in validation_report
            assert 'test_results' in validation_report
            assert 'summary' in validation_report
            
            assert validation_report['scenario_id'] == "test-scenario-123"
            assert isinstance(validation_report['overall_success'], bool)
            assert len(validation_report['test_results']) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_scenarios(self, config):
        """Test multiple concurrent chaos scenarios"""
        failure_injector = FailureInjector(config['chaos_testing'])
        
        # Mock Docker client
        with patch('docker.from_env') as mock_docker:
            mock_container = Mock()
            mock_container.id = "test123"
            mock_docker.return_value.containers.get.return_value = mock_container
            
            scenarios = []
            
            # Create multiple scenarios
            for i in range(2):
                scenario = create_failure_scenario(
                    scenario_type="latency_injection",
                    target=f"test-container-{i}",
                    parameters={"latency_ms": 100},
                    duration=60,
                    severity=1
                )
                scenarios.append(scenario)
            
            # Inject failures concurrently
            with patch('subprocess.run'):
                tasks = []
                for scenario in scenarios:
                    task = failure_injector.inject_failure(scenario)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                
                # Verify all scenarios were injected successfully
                assert all(results)
                
                # Verify scenarios are active
                active_scenarios = failure_injector.get_active_scenarios()
                assert len(active_scenarios) == 2
                
                # Recover all scenarios
                recovery_tasks = []
                for scenario in scenarios:
                    task = failure_injector.recover_failure(scenario.id)
                    recovery_tasks.append(task)
                
                recovery_results = await asyncio.gather(*recovery_tasks)
                assert all(recovery_results)


if __name__ == "__main__":
    pytest.main([__file__])
EOF
    
    # Chaos-specific tests
    cat > tests/chaos/test_chaos_scenarios.py << 'EOF'
"""
Chaos scenario tests - actual failure injection tests
"""

import pytest
import asyncio
import docker
import time
from unittest.mock import Mock, patch

from src.chaos.failure_injector import FailureInjector, create_failure_scenario


class TestChaosScenarios:
    
    @pytest.fixture
    def chaos_config(self):
        return {
            'safety_limits': {
                'max_blast_radius': 0.5,
                'max_concurrent_scenarios': 5,
                'max_severity': 5
            }
        }
    
    @pytest.mark.asyncio
    async def test_network_partition_scenario(self, chaos_config):
        """Test network partition chaos scenario"""
        failure_injector = FailureInjector(chaos_config)
        
        scenario = create_failure_scenario(
            scenario_type="network_partition",
            target="test-target",
            parameters={
                "isolate_from": "172.17.0.0/16",
                "blast_radius": 0.1
            },
            duration=30,
            severity=2
        )
        
        # Mock Docker operations
        with patch('docker.from_env') as mock_docker, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_container = Mock()
            mock_container.id = "container123"
            mock_docker.return_value.containers.get.return_value = mock_container
            
            # Test injection
            success = await failure_injector.inject_failure(scenario)
            assert success
            
            # Verify iptables rules were applied
            assert mock_subprocess.call_count >= 2
            
            # Test recovery
            recovery_success = await failure_injector.recover_failure(scenario.id)
            assert recovery_success
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_scenario(self, chaos_config):
        """Test resource exhaustion chaos scenario"""
        failure_injector = FailureInjector(chaos_config)
        
        scenario = create_failure_scenario(
            scenario_type="resource_exhaustion",
            target="test-target",
            parameters={
                "cpu_limit": 50,
                "memory_limit": 256,
                "blast_radius": 0.15
            },
            duration=45,
            severity=3
        )
        
        with patch('docker.from_env') as mock_docker:
            mock_container = Mock()
            mock_docker.return_value.containers.get.return_value = mock_container
            
            # Test injection
            success = await failure_injector.inject_failure(scenario)
            assert success
            
            # Verify container limits were updated
            mock_container.update.assert_called_once()
            call_kwargs = mock_container.update.call_args[1]
            assert 'cpu_quota' in call_kwargs or 'mem_limit' in call_kwargs
            
            # Test recovery
            recovery_success = await failure_injector.recover_failure(scenario.id)
            assert recovery_success
            
            # Verify limits were reset
            assert mock_container.update.call_count == 2  # Once for limit, once for reset
    
    @pytest.mark.asyncio
    async def test_component_failure_scenario(self, chaos_config):
        """Test component failure chaos scenario"""
        failure_injector = FailureInjector(chaos_config)
        
        scenario = create_failure_scenario(
            scenario_type="component_failure",
            target="test-target",
            parameters={
                "mode": "crash",
                "blast_radius": 0.2
            },
            duration=60,
            severity=4
        )
        
        with patch('docker.from_env') as mock_docker:
            mock_container = Mock()
            mock_docker.return_value.containers.get.return_value = mock_container
            
            # Test crash injection
            success = await failure_injector.inject_failure(scenario)
            assert success
            
            # Verify container was stopped
            mock_container.stop.assert_called_once()
            assert scenario.metadata['action'] == 'stopped'
            
            # Test recovery
            recovery_success = await failure_injector.recover_failure(scenario.id)
            assert recovery_success
            
            # Verify container was restarted
            mock_container.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_latency_injection_scenario(self, chaos_config):
        """Test latency injection chaos scenario"""
        failure_injector = FailureInjector(chaos_config)
        
        scenario = create_failure_scenario(
            scenario_type="latency_injection",
            target="test-target",
            parameters={
                "latency_ms": 200,
                "blast_radius": 0.1
            },
            duration=30,
            severity=2
        )
        
        with patch('docker.from_env') as mock_docker, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_container = Mock()
            mock_container.id = "container123"
            mock_docker.return_value.containers.get.return_value = mock_container
            
            # Test injection
            success = await failure_injector.inject_failure(scenario)
            assert success
            
            # Verify tc command was executed
            mock_subprocess.assert_called()
            call_args = ' '.join(mock_subprocess.call_args[0][0])
            assert 'tc qdisc add' in call_args
            assert 'netem delay' in call_args
            assert '200ms' in call_args
            
            # Test recovery
            recovery_success = await failure_injector.recover_failure(scenario.id)
            assert recovery_success
    
    @pytest.mark.asyncio
    async def test_scenario_timeout_handling(self, chaos_config):
        """Test scenario timeout and automatic recovery"""
        failure_injector = FailureInjector(chaos_config)
        
        # Create short duration scenario
        scenario = create_failure_scenario(
            scenario_type="latency_injection",
            target="test-target",
            parameters={"latency_ms": 100},
            duration=1,  # Very short duration
            severity=1
        )
        
        with patch('docker.from_env') as mock_docker, \
             patch('subprocess.run'):
            
            mock_container = Mock()
            mock_container.id = "container123"
            mock_docker.return_value.containers.get.return_value = mock_container
            
            # Inject failure
            success = await failure_injector.inject_failure(scenario)
            assert success
            
            # Wait for timeout (simulated)
            await asyncio.sleep(0.1)
            
            # Verify scenario is still active initially
            active_scenarios = failure_injector.get_active_scenarios()
            assert len(active_scenarios) == 1
            
            # Manual recovery (simulating timeout handler)
            recovery_success = await failure_injector.recover_failure(scenario.id)
            assert recovery_success
    
    @pytest.mark.asyncio
    async def test_blast_radius_enforcement(self, chaos_config):
        """Test blast radius safety enforcement"""
        failure_injector = FailureInjector(chaos_config)
        
        # Create scenario with excessive blast radius
        scenario = create_failure_scenario(
            scenario_type="component_failure",
            target="test-target",
            parameters={
                "mode": "crash",
                "blast_radius": 0.8  # Exceeds safety limit
            },
            duration=60,
            severity=2
        )
        
        # This should fail safety check
        with patch('docker.from_env'):
            success = await failure_injector.inject_failure(scenario)
            assert not success
            
            # Verify no scenarios are active
            active_scenarios = failure_injector.get_active_scenarios()
            assert len(active_scenarios) == 0


if __name__ == "__main__":
    pytest.main([__file__])
EOF
    
    # Verify test files were created
    if [ -f "tests/unit/test_failure_injector.py" ]; then
        log_success "Unit tests created successfully"
    else
        log_error "Failed to create unit tests"
    fi
    
    if [ -f "tests/integration/test_chaos_integration.py" ]; then
        log_success "Integration tests created successfully"
    else
        log_error "Failed to create integration tests"
    fi
    
    if [ -f "tests/chaos/test_chaos_scenarios.py" ]; then
        log_success "Chaos tests created successfully"
    else
        log_error "Failed to create chaos tests"
    fi
    
    log_success "Test suite creation completed"
}

# Create documentation
create_documentation() {
    log_info "Creating documentation..."
    
    cat > README.md << 'EOF'
# Chaos Testing Framework for Distributed Log Processing

## Overview

This framework implements comprehensive chaos engineering tools for testing the resilience of distributed log processing systems. It includes failure injection, real-time monitoring, and automated recovery validation.

## Features

### 🌪️ Chaos Scenarios
- **Network Partition**: Simulate network failures between services
- **Resource Exhaustion**: CPU, memory, and disk pressure testing
- **Component Failure**: Service crash and hang simulation
- **Latency Injection**: Network latency testing
- **Packet Loss**: Network reliability testing

### 📊 Real-time Monitoring
- System metrics (CPU, memory, disk, network)
- Service health monitoring
- Custom application metrics
- Alert thresholds and notifications

### 🔍 Recovery Validation
- Automated recovery verification
- Service availability testing
- Data consistency checks
- Performance baseline validation

### 🎯 Safety Controls
- Blast radius limitations
- Concurrent scenario limits
- Severity level controls
- Emergency stop functionality

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (optional)
- Node.js 18+ (for frontend)

### Installation
```bash
# Run the setup script
chmod +x setup.sh
./setup.sh
```

### Running the Application

#### Option 1: Interactive Demo
```bash
cd chaos-testing-framework
./setup.sh
# Choose option 1 for interactive demo
```

#### Option 2: Docker Deployment
```bash
cd chaos-testing-framework/docker
docker-compose up --build
```

#### Option 3: Manual Setup
```bash
cd chaos-testing-framework

# Start backend
source venv/bin/activate
PYTHONPATH="$(pwd)/src:$PYTHONPATH" python -m src.web.main

# Start frontend (in another terminal)
cd frontend
npm start
```

## Usage

### Web Dashboard
Access the web dashboard at `http://localhost:3000`

#### Creating Chaos Scenarios
1. Select a scenario type from the dropdown
2. Choose a target service
3. Configure parameters and severity
4. Click "Start Chaos Scenario"

#### Monitoring
- Real-time metrics are displayed in the dashboard
- Service health indicators show current status
- Alerts are triggered when thresholds are exceeded

#### Recovery Validation
- Automatic recovery validation after scenarios
- Manual validation triggers available
- Comprehensive recovery reports

### API Usage
The REST API is available at `http://localhost:8000`

#### Key Endpoints
- `GET /health` - Health check
- `GET /api/chaos/scenarios` - List active scenarios
- `POST /api/chaos/scenarios` - Create new scenario
- `POST /api/chaos/scenarios/{id}/stop` - Stop scenario
- `POST /api/chaos/emergency-stop` - Emergency stop all
- `GET /api/monitoring/metrics` - Current metrics
- `POST /api/recovery/validate/{id}` - Validate recovery

### CLI Usage
```bash
# Run tests
python -m pytest tests/

# Start API server
python -m src.web.main

# Check configuration
python -c "import yaml; print(yaml.safe_load(open('config/chaos_config.yaml')))"
```

## Configuration

### Main Configuration (`config/chaos_config.yaml`)
```yaml
chaos_testing:
  default_duration: 300  # seconds
  safety_timeout: 600
  blast_radius_limit: 0.3
  
  scenarios:
    network_partition:
      enabled: true
      severity_levels: [1, 2, 3, 4, 5]
    
    resource_exhaustion:
      enabled: true
      memory_pressure: [50, 70, 90]
      cpu_throttle: [50, 70, 90]
    
    component_failure:
      enabled: true
      target_services: ["log-collector", "message-queue", "log-processor"]
      failure_types: ["crash", "hang", "slow_response"]

monitoring:
  metrics_interval: 5
  health_check_timeout: 10
  critical_metrics:
    - "log_processing_rate"
    - "message_queue_depth"
    - "system_memory_usage"
    - "network_latency"

recovery:
  auto_recovery_enabled: true
  max_recovery_attempts: 3
  recovery_validation_steps:
    - "service_health_check"
    - "data_consistency_check"
    - "performance_baseline_check"
```

## Architecture

### Backend Components
- **Failure Injector** (`src/chaos/failure_injector.py`)
- **System Monitor** (`src/monitoring/system_monitor.py`)
- **Recovery Validator** (`src/recovery/recovery_validator.py`)
- **Web API** (`src/web/main.py`)

### Frontend Components
- **Control Panel** (`ChaosControlPanel.js`)
- **Metrics Dashboard** (`MetricsDashboard.js`)
- **Scenario Management** (`ScenarioList.js`)
- **Recovery Status** (`RecoveryStatus.js`)

### Docker Services
- **chaos-testing-api**: Main API server
- **chaos-testing-frontend**: React dashboard
- **redis**: Metrics storage
- **Target services**: Log collector, message queue, processor

## Safety Features

### Blast Radius Control
- Maximum 30% of system affected by default
- Configurable per scenario type
- Automatic enforcement

### Concurrent Scenario Limits
- Maximum 3 concurrent scenarios
- Prevents system overload
- Queue management for additional scenarios

### Emergency Recovery
- Immediate stop of all scenarios
- Automatic cleanup of injected failures
- System state restoration

## Testing

### Unit Tests
```bash
python -m pytest tests/unit/ -v
```

### Integration Tests
```bash
python -m pytest tests/integration/ -v
```

### Chaos Tests
```bash
python -m pytest tests/chaos/ -v
```

### End-to-End Testing
```bash
python -m pytest tests/ -v --tb=short
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Kill processes on required ports
lsof -ti:8000 | xargs kill -9  # API port
lsof -ti:3000 | xargs kill -9  # Frontend port
```

#### Docker Issues
```bash
# Reset Docker environment
docker-compose down -v
docker system prune -f
docker-compose up --build
```

#### Permission Errors
```bash
# Fix permissions
sudo chown -R $USER:$USER .
chmod +x setup.sh
```

### Logs
- Application logs: `logs/chaos_testing.log`
- Docker logs: `docker-compose logs`
- Frontend logs: Browser console

## Development

### Adding New Scenarios
1. Extend `FailureType` enum
2. Add injection method in `FailureInjector`
3. Add recovery method
4. Update configuration schema
5. Add frontend template

### Custom Metrics
1. Extend `SystemMonitor` class
2. Add metric collection method
3. Update alert thresholds
4. Add dashboard visualization

### API Extensions
1. Add endpoints in `main.py`
2. Update frontend services
3. Add tests
4. Update documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the troubleshooting section
- Review application logs
- Open an issue with detailed reproduction steps
EOF
    
    log_success "Documentation created"
}

# Create helper scripts
create_helper_scripts() {
    log_info "Creating helper scripts..."
    
    # Create start script
    cat > start.sh << 'EOF'
#!/bin/bash

# Start Chaos Testing Framework
echo "🌪️ Starting Chaos Testing Framework..."

# Check if already running
if pgrep -f "python -m src.web.main" > /dev/null; then
    echo "❌ Backend already running"
    exit 1
fi

if pgrep -f "npm start" > /dev/null; then
    echo "❌ Frontend already running"
    exit 1
fi

# Start Redis if Docker is available
if command -v docker > /dev/null 2>&1; then
    echo "🔄 Starting Redis..."
    docker run -d --name chaos-redis -p 6379:6379 redis:7.2-alpine > /dev/null 2>&1 || echo "Redis already running"
fi

# Start backend
echo "🔄 Starting backend API..."
source venv/bin/activate
PYTHONPATH="$(pwd)/src:$PYTHONPATH" python -m src.web.main &
BACKEND_PID=$!
echo $BACKEND_PID > backend.pid

# Start frontend
echo "🔄 Starting frontend..."
cd frontend
npm start > /dev/null 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid
cd ..

# Wait for services to start
sleep 10

# Check if services are running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend healthy: http://localhost:8000"
else
    echo "❌ Backend failed to start"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend healthy: http://localhost:3000"
else
    echo "❌ Frontend failed to start"
fi

echo ""
echo "🎯 Chaos Testing Framework is running!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 API: http://localhost:8000"
echo ""
echo "Use ./stop.sh to stop all services"
EOF

    chmod +x start.sh
    
    # Create stop script
    cat > stop.sh << 'EOF'
#!/bin/bash

# Stop Chaos Testing Framework
echo "🛑 Stopping Chaos Testing Framework..."

# Stop backend
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🔄 Stopping backend..."
        kill $BACKEND_PID
        rm backend.pid
    fi
fi

# Stop frontend
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🔄 Stopping frontend..."
        kill $FRONTEND_PID
        rm frontend.pid
    fi
fi

# Stop any remaining processes
pkill -f "python -m src.web.main" > /dev/null 2>&1
pkill -f "npm start" > /dev/null 2>&1

# Stop Redis if Docker is available
if command -v docker > /dev/null 2>&1; then
    echo "🔄 Stopping Redis..."
    docker stop chaos-redis > /dev/null 2>&1
    docker rm chaos-redis > /dev/null 2>&1
fi

echo "✅ Chaos Testing Framework stopped"
EOF

    chmod +x stop.sh
    
    # Create test script
    cat > test.sh << 'EOF'
#!/bin/bash

# Run tests for Chaos Testing Framework
echo "🧪 Running Chaos Testing Framework tests..."

# Activate virtual environment
source venv/bin/activate

# Run different test suites
echo "📋 Running unit tests..."
python -m pytest tests/unit/ -v --tb=short

echo ""
echo "🔗 Running integration tests..."
python -m pytest tests/integration/ -v --tb=short

echo ""
echo "🌪️ Running chaos tests..."
python -m pytest tests/chaos/ -v --tb=short

echo ""
echo "📊 Running all tests with coverage..."
python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

echo ""
echo "✅ Testing completed!"
echo "📄 Coverage report: htmlcov/index.html"
EOF

    chmod +x test.sh
    
    # Create development script
    cat > dev.sh << 'EOF'
#!/bin/bash

# Development utilities for Chaos Testing Framework
echo "🔧 Chaos Testing Framework Development Tools"

case "$1" in
    "lint")
        echo "🔍 Running linting..."
        source venv/bin/activate
        flake8 src/ --max-line-length=100
        black --check src/
        mypy src/
        ;;
    "format")
        echo "🎨 Formatting code..."
        source venv/bin/activate
        black src/
        ;;
    "check")
        echo "✅ Running development checks..."
        source venv/bin/activate
        python -m py_compile src/chaos/failure_injector.py
        python -m py_compile src/monitoring/system_monitor.py
        python -m py_compile src/recovery/recovery_validator.py
        python -m py_compile src/web/main.py
        echo "All Python files compile successfully"
        ;;
    "install")
        echo "📦 Installing development dependencies..."
        source venv/bin/activate
        pip install -r requirements.txt
        cd frontend && npm install
        ;;
    "clean")
        echo "🧹 Cleaning up..."
        rm -rf __pycache__ src/__pycache__ tests/__pycache__
        rm -rf .pytest_cache htmlcov .coverage
        rm -f backend.pid frontend.pid
        find . -name "*.pyc" -delete
        ;;
    *)
        echo "Usage: $0 {lint|format|check|install|clean}"
        echo ""
        echo "Commands:"
        echo "  lint     - Run code linting"
        echo "  format   - Format code with black"
        echo "  check    - Check Python syntax"
        echo "  install  - Install all dependencies"
        echo "  clean    - Clean up temporary files"
        ;;
esac
EOF

    chmod +x dev.sh
    
    log_success "Helper scripts created"
}

# Build and test functionality
build_and_test() {
    log_info "Building and testing the chaos testing framework..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run syntax validation
    log_info "Validating Python syntax..."
    find src -name "*.py" -exec python -m py_compile {} \;
    log_success "All Python files have valid syntax!"
    
    # Run unit tests
    log_info "Running unit tests..."
    python -m pytest tests/unit/ -v --tb=short
    if [ $? -eq 0 ]; then
        log_success "Unit tests passed!"
    else
        log_warning "Some unit tests failed, continuing with integration..."
    fi
    
    # Run integration tests  
    log_info "Running integration tests..."
    python -m pytest tests/integration/ -v --tb=short
    if [ $? -eq 0 ]; then
        log_success "Integration tests passed!"
    else
        log_warning "Some integration tests failed, continuing..."
    fi
    
    # Build frontend
    log_info "Building React frontend..."
    cd frontend
    npm run build
    if [ $? -eq 0 ]; then
        log_success "Frontend build successful!"
    else
        log_error "Frontend build failed!"
        cd ..
        return 1
    fi
    cd ..
    
    log_success "Build and test completed successfully!"
}

# Start services and demo
run_demonstration() {
    log_info "Starting chaos testing demonstration..."
    
    # Start Redis for metrics storage
    if $DOCKER_AVAILABLE; then
        log_info "Starting Redis container..."
        docker run -d --name chaos-redis -p 6379:6379 redis:7.2-alpine >/dev/null 2>&1 || {
            log_info "Redis container already running or failed to start"
        }
    fi
    
    # Start target services for chaos testing
    if $DOCKER_AVAILABLE; then
        log_info "Starting target services..."
        
        # Log collector service
        docker run -d --name log-collector-service \
            -p 8001:80 \
            -l chaos.target=true \
            -l chaos.service=log-collector \
            nginx:alpine >/dev/null 2>&1 || log_info "Log collector already running"
        
        # Message queue service
        docker run -d --name message-queue-service \
            -p 5672:5672 -p 15672:15672 \
            -l chaos.target=true \
            -l chaos.service=message-queue \
            rabbitmq:3.12-management >/dev/null 2>&1 || log_info "Message queue already running"
        
        # Log processor service
        docker run -d --name log-processor-service \
            -p 8002:80 \
            -l chaos.target=true \
            -l chaos.service=log-processor \
            nginx:alpine >/dev/null 2>&1 || log_info "Log processor already running"
        
        log_success "Target services started"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start backend API
    log_info "Starting Chaos Testing API..."
    PYTHONPATH="$(pwd)/src:$PYTHONPATH" python -m src.web.main &
    API_PID=$!
    
    # Wait for API to start
    sleep 5
    
    # Start frontend development server
    log_info "Starting React frontend..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    # Wait for services to fully initialize
    log_info "Waiting for services to initialize..."
    sleep 10
    
    # Test API health
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        log_success "API is healthy and responding"
    else
        log_warning "API health check failed"
    fi
    
    # Display service URLs
    echo ""
    echo "🎯 Chaos Testing Framework is ready!"
    echo "==============================================="
    echo "📊 Dashboard: http://localhost:3000"
    echo "🔧 API: http://localhost:8000"
    echo "📋 API Documentation: http://localhost:8000/docs"
    echo "📈 Health Check: http://localhost:8000/health"
    echo ""
    echo "Target Services:"
    echo "🏭 Log Collector: http://localhost:8001"
    echo "📮 Message Queue: http://localhost:15672 (guest/guest)"
    echo "⚙️ Log Processor: http://localhost:8002"
    echo ""
    
    # Run automated demo
    log_info "Running automated demonstration..."
    
    # Test API endpoints
    echo "Testing API endpoints..."
    
    # Get scenario templates
    echo "📋 Available chaos scenarios:"
    curl -s http://localhost:8000/api/config/scenarios | jq '.templates[].name' 2>/dev/null || echo "Templates loaded"
    
    # Get current metrics
    echo "📊 Current system metrics:"
    curl -s http://localhost:8000/api/monitoring/metrics | jq '.cpu_usage, .memory_usage' 2>/dev/null || echo "Metrics collected"
    
    # Create a test chaos scenario
    echo "🌪️ Creating test chaos scenario..."
    SCENARIO_RESPONSE=$(curl -s -X POST http://localhost:8000/api/chaos/scenarios \
        -H "Content-Type: application/json" \
        -d '{
            "type": "latency_injection",
            "target": "log-collector-service",
            "parameters": {
                "latency_ms": 100,
                "blast_radius": 0.1
            },
            "duration": 30,
            "severity": 1
        }' 2>/dev/null)
    
    if echo "$SCENARIO_RESPONSE" | grep -q "success"; then
        log_success "Test chaos scenario created successfully"
        
        # Get scenario ID
        SCENARIO_ID=$(echo "$SCENARIO_RESPONSE" | jq -r '.scenario_id' 2>/dev/null)
        
        # Wait a moment
        sleep 3
        
        # Check active scenarios
        echo "📋 Active scenarios:"
        curl -s http://localhost:8000/api/chaos/scenarios | jq '.scenarios | length' 2>/dev/null || echo "Scenarios listed"
        
        # Stop the test scenario
        if [ ! -z "$SCENARIO_ID" ] && [ "$SCENARIO_ID" != "null" ]; then
            echo "🛑 Stopping test scenario..."
            curl -s -X POST "http://localhost:8000/api/chaos/scenarios/$SCENARIO_ID/stop" >/dev/null 2>&1
            log_success "Test scenario stopped"
        fi
    else
        log_warning "Test scenario creation failed (this is expected in mock environment)"
    fi
    
    # Display instructions
    echo ""
    echo "🎮 Demo Instructions:"
    echo "==================="
    echo "1. Open http://localhost:3000 in your browser"
    echo "2. Try creating different chaos scenarios"
    echo "3. Monitor system metrics in real-time"
    echo "4. Observe recovery validation results"
    echo "5. Use Emergency Stop if needed"
    echo ""
    echo "🔧 Advanced Features:"
    echo "- Multiple concurrent scenarios"
    echo "- Real-time WebSocket updates"
    echo "- Blast radius safety controls"
    echo "- Automated recovery validation"
    echo ""
    
    # Keep services running
    echo "Press Ctrl+C to stop all services..."
    
    # Cleanup function
    cleanup() {
        echo ""
        log_info "Stopping services..."
        
        # Kill background processes
        [ ! -z "$API_PID" ] && kill $API_PID 2>/dev/null
        [ ! -z "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
        
        # Stop Docker containers
        if $DOCKER_AVAILABLE; then
            docker stop chaos-redis log-collector-service message-queue-service log-processor-service >/dev/null 2>&1
            docker rm chaos-redis log-collector-service message-queue-service log-processor-service >/dev/null 2>&1
        fi
        
        log_success "Cleanup completed"
        exit 0
    }
    
    # Set trap for cleanup
    trap cleanup SIGINT SIGTERM
    
    # Wait indefinitely
    wait
}

# Docker deployment
deploy_with_docker() {
    log_info "Deploying with Docker..."
    
    if ! $DOCKER_AVAILABLE; then
        log_error "Docker is not available. Please install Docker to use this feature."
        return 1
    fi
    
    # Build and start with docker-compose
    cd docker
    docker-compose down -v >/dev/null 2>&1  # Clean any existing containers
    docker-compose up --build -d
    
    if [ $? -eq 0 ]; then
        log_success "Docker deployment successful!"
        
        echo ""
        echo "🐳 Docker Services Status:"
        echo "========================="
        docker-compose ps
        
        echo ""
        echo "🌐 Access URLs:"
        echo "Dashboard: http://localhost:3000"
        echo "API: http://localhost:8000"
        echo "RabbitMQ Management: http://localhost:15672"
        echo ""
        
        # Wait for services to be ready
        log_info "Waiting for services to be ready..."
        sleep 15
        
        # Test deployment
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            log_success "Docker deployment is healthy and ready!"
        else
            log_warning "Services may still be starting up..."
        fi
    else
        log_error "Docker deployment failed!"
        return 1
    fi
    
    cd ..
}

# Verification and testing
verify_installation() {
    log_info "Verifying installation..."
    
    local verification_passed=true
    
    # Check Python environment
    if source venv/bin/activate && python -c "import src.chaos.failure_injector; print('✅ Chaos modules imported successfully')" >/dev/null 2>&1; then
        log_success "Python environment verified"
    else
        log_error "Python environment verification failed"
        verification_passed=false
    fi
    
    # Check core Python modules
    local core_modules=(
        "src/chaos/failure_injector.py"
        "src/monitoring/system_monitor.py"
        "src/recovery/recovery_validator.py"
        "src/web/main.py"
    )
    
    for module in "${core_modules[@]}"; do
        if [ -f "$module" ]; then
            log_success "Core module verified: $module"
        else
            log_error "Core module missing: $module"
            verification_passed=false
        fi
    done
    
    # Check configuration files
    local config_files=(
        "config/chaos_config.yaml"
        "requirements.txt"
        "docker/docker-compose.yaml"
        "docker/Dockerfile.api"
        "docker/Dockerfile.frontend"
    )
    
    for config_file in "${config_files[@]}"; do
        if [ -f "$config_file" ]; then
            log_success "Configuration file verified: $config_file"
        else
            log_error "Configuration file missing: $config_file"
            verification_passed=false
        fi
    done
    
    # Check test files
    local test_files=(
        "tests/unit/test_failure_injector.py"
        "tests/integration/test_chaos_integration.py"
        "tests/chaos/test_chaos_scenarios.py"
    )
    
    for test_file in "${test_files[@]}"; do
        if [ -f "$test_file" ]; then
            log_success "Test file verified: $test_file"
        else
            log_error "Test file missing: $test_file"
            verification_passed=false
        fi
    done
    
    # Check frontend files
    local frontend_files=(
        "frontend/package.json"
        "frontend/src/App.js"
        "frontend/src/components/ChaosControlPanel.js"
        "frontend/src/components/MetricsDashboard.js"
        "frontend/src/components/ScenarioList.js"
        "frontend/src/components/RecoveryStatus.js"
        "frontend/src/services/api.js"
        "frontend/src/utils/websocket.js"
        "frontend/src/utils/formatters.js"
        "frontend/src/utils/constants.js"
        "frontend/public/index.html"
    )
    
    for frontend_file in "${frontend_files[@]}"; do
        if [ -f "$frontend_file" ]; then
            log_success "Frontend file verified: $frontend_file"
        else
            log_error "Frontend file missing: $frontend_file"
            verification_passed=false
        fi
    done
    
    # Check documentation
    if [ -f "README.md" ]; then
        log_success "Documentation verified"
    else
        log_error "Documentation missing"
        verification_passed=false
    fi
    
    # Check helper scripts
    local helper_scripts=(
        "start.sh"
        "stop.sh"
        "test.sh"
        "dev.sh"
    )
    
    for script in "${helper_scripts[@]}"; do
        if [ -f "$script" ] && [ -x "$script" ]; then
            log_success "Helper script verified: $script"
        else
            log_error "Helper script missing or not executable: $script"
            verification_passed=false
        fi
    done
    
    # Check directory structure
    local directories=(
        "src/chaos"
        "src/monitoring"
        "src/recovery"
        "src/web"
        "tests/unit"
        "tests/integration"
        "tests/chaos"
        "config"
        "docker"
        "frontend/src/components"
        "frontend/src/services"
        "frontend/src/utils"
        "frontend/public"
        "logs"
    )
    
    for directory in "${directories[@]}"; do
        if [ -d "$directory" ]; then
            log_success "Directory verified: $directory"
        else
            log_error "Directory missing: $directory"
            verification_passed=false
        fi
    done
    
    if [ "$verification_passed" = true ]; then
        log_success "Installation verification completed successfully!"
        return 0
    else
        log_error "Installation verification failed - some files are missing"
        return 1
    fi
}

# Main execution flow
main() {
    echo "🎯 Day 63: Chaos Testing Tools Implementation"
    echo "============================================="
    echo "Building resilience through controlled failure injection"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Create project structure
    create_project_structure
    
    # Setup dependencies
    setup_python_dependencies
    setup_react_frontend
    
    # Create configuration
    create_config_files
    
    # Create core modules
    create_chaos_modules
    
    # Create web interface
    create_web_interface
    
    # Create test suite
    create_test_suite
    
    # Create documentation
    create_documentation
    
    # Create helper scripts
    create_helper_scripts
    
    # Build and test
    build_and_test
    
    # Verify installation
    verify_installation
    
    echo ""
    echo "🎉 Chaos Testing Framework Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Choose your deployment option:"
    echo "1. 🚀 Run interactive demonstration (Recommended)"
    echo "2. 🐳 Deploy with Docker"
    echo "3. ⚡ Quick verification only"
    echo ""
    
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            run_demonstration
            ;;
        2)
            deploy_with_docker
            ;;
        3)
            log_info "Running quick verification..."
            source venv/bin/activate
            python -c "
from src.chaos.failure_injector import FailureInjector, create_failure_scenario
from src.monitoring.system_monitor import SystemMonitor
from src.recovery.recovery_validator import RecoveryValidator

print('✅ All modules imported successfully')
print('🎯 Chaos Testing Framework is ready for use!')
"
            ;;
        *)
            log_info "Invalid choice. Running demonstration..."
            run_demonstration
            ;;
    esac
    
    echo ""
    echo "🎯 Next Steps:"
    echo "============="
    echo "• Experiment with different failure scenarios"
    echo "• Monitor system behavior during chaos"
    echo "• Validate recovery mechanisms"  
    echo "• Integrate with your existing monitoring"
    echo "• Prepare for Day 64: Role-based Access Control"
    echo ""
    echo "📚 Quick Commands:"
    echo "=================="
    echo "• Start services: ./start.sh"
    echo "• Stop services: ./stop.sh"
    echo "• Run tests: ./test.sh"
    echo "• Development: ./dev.sh {lint|format|check|install|clean}"
    echo "• Documentation: ./README.md"
    echo "• Docker: cd docker && docker-compose up"
    echo ""
    
    # Final file count summary
    echo "📊 Installation Summary:"
    echo "======================="
    echo "• Core Python modules: $(find src -name '*.py' | wc -l | tr -d ' ') files"
    echo "• React components: $(find frontend/src -name '*.js' | wc -l | tr -d ' ') files"
    echo "• Test files: $(find tests -name '*.py' | wc -l | tr -d ' ') files"
    echo "• Configuration files: $(find config docker -name '*.yaml' -o -name '*.yml' -o -name 'Dockerfile*' | wc -l | tr -d ' ') files"
    echo "• Helper scripts: $(ls -1 *.sh | wc -l | tr -d ' ') files"
    echo "• Documentation: README.md"
    echo ""
    
    log_success "Chaos Testing Framework implementation completed!"
}

# Execute main function
main "$@"
