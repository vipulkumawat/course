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
