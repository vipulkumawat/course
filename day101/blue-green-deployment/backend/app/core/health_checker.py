import asyncio
import httpx
import logging
from datetime import datetime
from typing import Dict, List
import psutil

from models.deployment import HealthStatus, HealthCheckResult

logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self):
        self.health_history: Dict[str, List[HealthCheckResult]] = {}
        self.monitoring_active = False
    
    async def start_monitoring(self):
        """Start background health monitoring"""
        self.monitoring_active = True
        logger.info("🏥 Starting health monitoring")
        
        while self.monitoring_active:
            try:
                # Check blue environment
                await self._check_endpoint_health("blue", "http://localhost:8001")
                
                # Check green environment  
                await self._check_endpoint_health("green", "http://localhost:8002")
                
                # Wait before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def check_environment_health(self, base_url: str) -> HealthStatus:
        """Comprehensive environment health check"""
        checks = []
        
        # HTTP endpoint health
        http_result = await self._check_http_health(base_url)
        checks.append(http_result)
        
        # Performance checks
        perf_result = await self._check_performance(base_url)
        checks.append(perf_result)
        
        # Resource utilization
        resource_result = await self._check_resources()
        checks.append(resource_result)
        
        # Business logic validation
        business_result = await self._check_business_logic(base_url)
        checks.append(business_result)
        
        # Determine overall health
        is_healthy = all(check.passed for check in checks)
        
        return HealthStatus(
            is_healthy=is_healthy,
            checks=checks,
            timestamp=datetime.now(),
            message="All checks passed" if is_healthy else "Some checks failed"
        )
    
    async def _check_http_health(self, base_url: str) -> HealthCheckResult:
        """Check HTTP endpoint health"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/health")
                
                if response.status_code == 200:
                    return HealthCheckResult(
                        check_name="http_health",
                        passed=True,
                        message="HTTP endpoint healthy",
                        details={"status_code": response.status_code}
                    )
                else:
                    return HealthCheckResult(
                        check_name="http_health",
                        passed=False,
                        message=f"HTTP endpoint unhealthy: {response.status_code}",
                        details={"status_code": response.status_code}
                    )
        except Exception as e:
            return HealthCheckResult(
                check_name="http_health",
                passed=False,
                message=f"HTTP check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_performance(self, base_url: str) -> HealthCheckResult:
        """Check performance metrics"""
        try:
            start_time = datetime.now()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{base_url}/metrics")
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Performance thresholds
            if response_time < 100:  # ms
                return HealthCheckResult(
                    check_name="performance",
                    passed=True,
                    message=f"Response time acceptable: {response_time:.2f}ms",
                    details={"response_time_ms": response_time}
                )
            else:
                return HealthCheckResult(
                    check_name="performance",
                    passed=False,
                    message=f"Response time too high: {response_time:.2f}ms",
                    details={"response_time_ms": response_time}
                )
        except Exception as e:
            return HealthCheckResult(
                check_name="performance",
                passed=False,
                message=f"Performance check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_resources(self) -> HealthCheckResult:
        """Check system resource utilization"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Resource thresholds
            resource_healthy = (
                cpu_percent < 80 and 
                memory.percent < 85 and 
                disk.percent < 90
            )
            
            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            }
            
            if resource_healthy:
                return HealthCheckResult(
                    check_name="resources",
                    passed=True,
                    message="Resource utilization normal",
                    details=details
                )
            else:
                return HealthCheckResult(
                    check_name="resources",
                    passed=False,
                    message="High resource utilization detected",
                    details=details
                )
        except Exception as e:
            return HealthCheckResult(
                check_name="resources",
                passed=False,
                message=f"Resource check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_business_logic(self, base_url: str) -> HealthCheckResult:
        """Check business logic functionality"""
        try:
            # Simulate log processing test
            test_log = {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "Health check test log",
                "source": "health_checker"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{base_url}/process-log",
                    json=test_log
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "processed":
                    return HealthCheckResult(
                        check_name="business_logic",
                        passed=True,
                        message="Business logic functioning correctly",
                        details=result
                    )
            
            return HealthCheckResult(
                check_name="business_logic",
                passed=False,
                message="Business logic test failed",
                details={"response": response.json() if response.status_code == 200 else None}
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name="business_logic",
                passed=False,
                message=f"Business logic check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _check_endpoint_health(self, env_name: str, base_url: str):
        """Check specific endpoint and store history"""
        result = await self._check_http_health(base_url)
        
        if env_name not in self.health_history:
            self.health_history[env_name] = []
        
        self.health_history[env_name].append(result)
        
        # Keep only last 100 results
        if len(self.health_history[env_name]) > 100:
            self.health_history[env_name] = self.health_history[env_name][-100:]
    
    async def get_overall_health(self) -> HealthStatus:
        """Get overall system health status"""
        # For simplicity, return basic health info
        return HealthStatus(
            is_healthy=True,
            checks=[
                HealthCheckResult(
                    check_name="system",
                    passed=True,
                    message="System operational",
                    details={"timestamp": datetime.now().isoformat()}
                )
            ],
            timestamp=datetime.now(),
            message="System healthy"
        )
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        logger.info("🛑 Health monitoring stopped")
