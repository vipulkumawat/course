from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional

class Environment(Enum):
    BLUE = "blue"
    GREEN = "green"

class DeploymentState(Enum):
    STABLE = "stable"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"

class HealthCheckResult(BaseModel):
    check_name: str
    passed: bool
    message: str
    details: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()

class HealthStatus(BaseModel):
    is_healthy: bool
    checks: List[HealthCheckResult] = []
    timestamp: datetime = datetime.now()
    message: str = ""

class DeploymentRequest(BaseModel):
    version: str
    config: Dict[str, Any] = {}
    force: bool = False

class DeploymentStatus(BaseModel):
    deployment_id: str
    state: DeploymentState
    active_environment: Environment = Environment.BLUE
    version: str = "1.0.0"
    health_status: Optional[HealthStatus] = None
    message: str = ""
    timestamp: datetime = datetime.now()
    
    class Config:
        use_enum_values = True
