"""
Deployment Validator
Validates deployments and triggers rollback on failures
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from kubernetes import client

logger = logging.getLogger(__name__)


class DeploymentValidator:
    def __init__(self, k8s_apps_v1, k8s_core_v1, config: Dict):
        self.k8s_apps_v1 = k8s_apps_v1
        self.k8s_core_v1 = k8s_core_v1
        self.config = config
        
    async def validate_deployment(self, deployment_name: str, namespace: str) -> bool:
        """Validate a deployment is healthy"""
        logger.info(f"🔍 Validating deployment: {deployment_name}")
        
        # Check deployment status
        health_checks = [
            self._check_replicas_ready(deployment_name, namespace),
            self._check_pods_running(deployment_name, namespace),
            self._check_recent_restarts(deployment_name, namespace)
        ]
        
        results = await asyncio.gather(*health_checks, return_exceptions=True)
        
        if all(results):
            logger.info(f"✅ Deployment {deployment_name} is healthy")
            return True
        else:
            logger.error(f"❌ Deployment {deployment_name} validation failed")
            return False
            
    async def _check_replicas_ready(self, deployment_name: str, namespace: str) -> bool:
        """Check if all replicas are ready"""
        try:
            deployment = self.k8s_apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=namespace
            )
            
            desired = deployment.spec.replicas
            ready = deployment.status.ready_replicas or 0
            
            if ready >= desired:
                logger.info(f"  ✓ Replicas ready: {ready}/{desired}")
                return True
            else:
                logger.warning(f"  ✗ Replicas not ready: {ready}/{desired}")
                return False
        except Exception as e:
            logger.error(f"  Error checking replicas: {e}")
            return False
            
    async def _check_pods_running(self, deployment_name: str, namespace: str) -> bool:
        """Check if pods are running"""
        try:
            pods = self.k8s_core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app={deployment_name}"
            )
            
            running_pods = sum(1 for pod in pods.items if pod.status.phase == "Running")
            
            if running_pods > 0:
                logger.info(f"  ✓ Pods running: {running_pods}")
                return True
            else:
                logger.warning("  ✗ No pods running")
                return False
        except Exception as e:
            logger.error(f"  Error checking pods: {e}")
            return False
            
    async def _check_recent_restarts(self, deployment_name: str, namespace: str) -> bool:
        """Check for excessive pod restarts"""
        try:
            pods = self.k8s_core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app={deployment_name}"
            )
            
            for pod in pods.items:
                for container_status in pod.status.container_statuses or []:
                    restart_count = container_status.restart_count
                    if restart_count > 5:
                        logger.warning(f"  ✗ Excessive restarts: {restart_count}")
                        return False
                        
            logger.info("  ✓ No excessive restarts")
            return True
        except Exception as e:
            logger.error(f"  Error checking restarts: {e}")
            return False
            
    async def rollback_deployment(self, deployment_name: str, namespace: str):
        """Rollback a deployment to previous version"""
        logger.info(f"🔄 Rolling back deployment: {deployment_name}")
        
        try:
            # Trigger rollback using Kubernetes API
            body = {
                'spec': {
                    'rollbackTo': {
                        'revision': 0  # Previous revision
                    }
                }
            }
            
            self.k8s_apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=body
            )
            
            logger.info(f"✅ Rollback initiated for {deployment_name}")
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
