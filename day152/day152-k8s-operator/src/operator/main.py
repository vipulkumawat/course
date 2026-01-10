"""
Kubernetes Operator for Log Platform Management
Main operator logic with reconciliation loops
"""
import asyncio
import kopf
import logging
from kubernetes import client, config
from datetime import datetime
from typing import Dict, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogProcessorOperator:
    """Main operator class for LogProcessor resources"""
    
    def __init__(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        
        self.apps_api = client.AppsV1Api()
        self.core_api = client.CoreV1Api()
        self.metrics = {
            'reconciliations': 0,
            'scaling_events': 0,
            'errors': 0
        }
    
    def create_deployment(self, name: str, namespace: str, spec: Dict[str, Any]) -> Dict:
        """Create Kubernetes Deployment for LogProcessor"""
        replicas = spec.get('replicas', 1)
        log_level = spec.get('logLevel', 'INFO')
        resources_spec = spec.get('resources', {})
        
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=f"{name}-deployment",
                namespace=namespace,
                labels={
                    'app': 'log-processor',
                    'processor': name,
                    'managed-by': 'log-operator'
                }
            ),
            spec=client.V1DeploymentSpec(
                replicas=replicas,
                selector=client.V1LabelSelector(
                    match_labels={'app': 'log-processor', 'processor': name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={'app': 'log-processor', 'processor': name}
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name='log-processor',
                                image='log-processor:latest',
                                env=[
                                    client.V1EnvVar(name='LOG_LEVEL', value=log_level),
                                    client.V1EnvVar(name='PROCESSOR_NAME', value=name)
                                ],
                                resources=client.V1ResourceRequirements(
                                    requests={
                                        'memory': resources_spec.get('memory', '512Mi'),
                                        'cpu': resources_spec.get('cpu', '250m')
                                    },
                                    limits={
                                        'memory': resources_spec.get('memory', '512Mi'),
                                        'cpu': resources_spec.get('cpu', '500m')
                                    }
                                ),
                                ports=[client.V1ContainerPort(container_port=8080)],
                                liveness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(
                                        path='/health',
                                        port=8080
                                    ),
                                    initial_delay_seconds=10,
                                    period_seconds=10
                                )
                            )
                        ]
                    )
                )
            )
        )
        return deployment
    
    def create_service(self, name: str, namespace: str) -> Dict:
        """Create Kubernetes Service for LogProcessor"""
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=f"{name}-service",
                namespace=namespace
            ),
            spec=client.V1ServiceSpec(
                selector={'app': 'log-processor', 'processor': name},
                ports=[
                    client.V1ServicePort(
                        port=8080,
                        target_port=8080,
                        name='http'
                    )
                ],
                type='ClusterIP'
            )
        )
        return service


# Initialize operator
operator = LogProcessorOperator()


@kopf.on.create('logs.platform.io', 'v1', 'logprocessors')
async def create_logprocessor(spec, name, namespace, logger, **kwargs):
    """Handle LogProcessor creation"""
    logger.info(f"Creating LogProcessor: {name} in namespace: {namespace}")
    operator.metrics['reconciliations'] += 1
    
    try:
        # Create Deployment
        deployment = operator.create_deployment(name, namespace, spec)
        operator.apps_api.create_namespaced_deployment(
            namespace=namespace,
            body=deployment
        )
        logger.info(f"✅ Created Deployment for {name}")
        
        # Create Service
        service = operator.create_service(name, namespace)
        operator.core_api.create_namespaced_service(
            namespace=namespace,
            body=service
        )
        logger.info(f"✅ Created Service for {name}")
        
        return {
            'state': 'Provisioning',
            'replicas': spec.get('replicas', 1),
            'readyReplicas': 0,
            'conditions': [{
                'type': 'Created',
                'status': 'True',
                'lastTransitionTime': datetime.now().isoformat(),
                'message': 'Resources created successfully'
            }]
        }
    
    except Exception as e:
        operator.metrics['errors'] += 1
        logger.error(f"Error creating LogProcessor {name}: {str(e)}")
        raise


@kopf.on.update('logs.platform.io', 'v1', 'logprocessors')
async def update_logprocessor(spec, old, new, name, namespace, logger, **kwargs):
    """Handle LogProcessor updates"""
    logger.info(f"Updating LogProcessor: {name}")
    operator.metrics['reconciliations'] += 1
    
    old_replicas = old.get('spec', {}).get('replicas', 1)
    new_replicas = spec.get('replicas', 1)
    
    if old_replicas != new_replicas:
        logger.info(f"Scaling {name} from {old_replicas} to {new_replicas} replicas")
        operator.metrics['scaling_events'] += 1
        
        try:
            # Update deployment replicas
            deployment = operator.apps_api.read_namespaced_deployment(
                name=f"{name}-deployment",
                namespace=namespace
            )
            deployment.spec.replicas = new_replicas
            
            operator.apps_api.patch_namespaced_deployment(
                name=f"{name}-deployment",
                namespace=namespace,
                body=deployment
            )
            logger.info(f"✅ Scaled {name} to {new_replicas} replicas")
            
        except Exception as e:
            operator.metrics['errors'] += 1
            logger.error(f"Error scaling {name}: {str(e)}")
            raise
    
    return {
        'state': 'Updating',
        'replicas': new_replicas
    }


@kopf.on.delete('logs.platform.io', 'v1', 'logprocessors')
async def delete_logprocessor(name, namespace, logger, **kwargs):
    """Handle LogProcessor deletion"""
    logger.info(f"Deleting LogProcessor: {name}")
    
    try:
        # Delete Deployment
        operator.apps_api.delete_namespaced_deployment(
            name=f"{name}-deployment",
            namespace=namespace
        )
        logger.info(f"✅ Deleted Deployment for {name}")
        
        # Delete Service
        operator.core_api.delete_namespaced_service(
            name=f"{name}-service",
            namespace=namespace
        )
        logger.info(f"✅ Deleted Service for {name}")
        
    except client.exceptions.ApiException as e:
        if e.status != 404:  # Ignore not found errors
            logger.error(f"Error deleting LogProcessor {name}: {str(e)}")
            raise


@kopf.timer('logs.platform.io', 'v1', 'logprocessors', interval=30.0)
async def monitor_logprocessor(spec, name, namespace, logger, **kwargs):
    """Periodic health check and auto-scaling"""
    try:
        deployment = operator.apps_api.read_namespaced_deployment(
            name=f"{name}-deployment",
            namespace=namespace
        )
        
        ready_replicas = deployment.status.ready_replicas or 0
        desired_replicas = deployment.spec.replicas
        
        # Check auto-scaling settings
        auto_scaling = spec.get('autoScaling', {})
        if auto_scaling.get('enabled', False):
            # Simulate queue depth check (would integrate with actual metrics)
            simulated_queue_depth = 5000  # Replace with actual metric
            target_queue_depth = auto_scaling.get('targetQueueDepth', 10000)
            
            min_replicas = auto_scaling.get('minReplicas', 1)
            max_replicas = auto_scaling.get('maxReplicas', 10)
            
            if simulated_queue_depth > target_queue_depth and desired_replicas < max_replicas:
                new_replicas = min(desired_replicas + 1, max_replicas)
                logger.info(f"🔼 Auto-scaling {name} from {desired_replicas} to {new_replicas}")
                operator.metrics['scaling_events'] += 1
                
                deployment.spec.replicas = new_replicas
                operator.apps_api.patch_namespaced_deployment(
                    name=f"{name}-deployment",
                    namespace=namespace,
                    body=deployment
                )
        
        # Log current status
        logger.info(f"📊 {name}: {ready_replicas}/{desired_replicas} replicas ready")
        
    except Exception as e:
        logger.error(f"Error monitoring {name}: {str(e)}")


@kopf.on.startup()
async def startup_handler(logger, **kwargs):
    """Operator startup handler"""
    logger.info("🚀 Log Platform Operator started successfully")
    logger.info(f"📊 Monitoring CustomResources: LogProcessor, LogCollector")


if __name__ == '__main__':
    kopf.run()
