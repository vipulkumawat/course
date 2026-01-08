"""
GitOps Controller for Distributed Log Processing Platform
Continuously syncs Git repository state with Kubernetes cluster
"""
import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

import git
import yaml
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitOpsController:
    def __init__(self, config_dict: Dict):
        self.config = config_dict
        self.git_repo = None
        self.k8s_apps_v1 = None
        self.k8s_core_v1 = None
        self.running = False
        self.last_sync_commit = None
        self.deployment_history = []
        
    async def initialize(self):
        """Initialize Git repository and Kubernetes clients"""
        logger.info("Initializing GitOps Controller...")
        
        # Initialize Kubernetes clients
        try:
            config.load_kube_config()
        except:
            # Fallback to in-cluster config
            config.load_incluster_config()
            
        self.k8s_apps_v1 = client.AppsV1Api()
        self.k8s_core_v1 = client.CoreV1Api()
        
        # Clone Git repository
        repo_url = self.config['git']['repository_url']
        repo_path = Path("/tmp/gitops-repo")
        
        if repo_path.exists():
            self.git_repo = git.Repo(repo_path)
            self.git_repo.remotes.origin.pull()
        else:
            self.git_repo = git.Repo.clone_from(repo_url, repo_path)
            
        logger.info(f"✅ Controller initialized. Watching {repo_url}")
        
    async def reconciliation_loop(self):
        """Main reconciliation loop - continuously sync Git to cluster"""
        self.running = True
        sync_interval = self.config['gitops']['sync_interval']
        
        logger.info(f"🔄 Starting reconciliation loop (interval: {sync_interval}s)")
        
        while self.running:
            try:
                await self._reconcile()
                await asyncio.sleep(sync_interval)
            except Exception as e:
                logger.error(f"❌ Reconciliation error: {e}")
                await asyncio.sleep(sync_interval)
                
    async def _reconcile(self):
        """Reconcile Git state with cluster state"""
        # Pull latest changes from Git
        self.git_repo.remotes.origin.pull()
        current_commit = self.git_repo.head.commit.hexsha
        
        # Check if there are new changes
        if current_commit == self.last_sync_commit:
            logger.debug("No new changes in Git")
            return
            
        logger.info(f"🔍 New commit detected: {current_commit[:8]}")
        
        # Get desired state from Git
        git_manifests = self._load_git_manifests()
        
        # Get current cluster state
        cluster_state = await self._get_cluster_state()
        
        # Calculate diff and apply changes
        changes = self._calculate_diff(git_manifests, cluster_state)
        
        if changes:
            logger.info(f"📝 Applying {len(changes)} changes...")
            success = await self._apply_changes(changes)
            
            if success:
                self.last_sync_commit = current_commit
                self._record_deployment(current_commit, changes, success=True)
                logger.info("✅ Reconciliation complete")
            else:
                logger.error("❌ Reconciliation failed, will retry")
        else:
            self.last_sync_commit = current_commit
            logger.info("✨ Cluster state matches Git - no changes needed")
            
    def _load_git_manifests(self) -> Dict:
        """Load Kubernetes manifests from Git repository"""
        manifests = {}
        repo_path = Path(self.git_repo.working_dir)
        
        # Load base manifests
        base_path = repo_path / "manifests" / "base"
        if base_path.exists():
            for yaml_file in base_path.rglob("*.yaml"):
                with open(yaml_file, 'r') as f:
                    doc = yaml.safe_load(f)
                    if doc:
                        key = f"{doc['kind']}/{doc['metadata']['name']}"
                        manifests[key] = doc
                        
        return manifests
        
    async def _get_cluster_state(self) -> Dict:
        """Get current state of resources in cluster"""
        state = {}
        namespace = self.config['kubernetes']['namespace']
        
        try:
            # Get Deployments
            deployments = self.k8s_apps_v1.list_namespaced_deployment(namespace)
            for dep in deployments.items:
                key = f"Deployment/{dep.metadata.name}"
                state[key] = {
                    'replicas': dep.spec.replicas,
                    'image': dep.spec.template.spec.containers[0].image,
                    'annotations': dep.metadata.annotations or {}
                }
                
            # Get Services
            services = self.k8s_core_v1.list_namespaced_service(namespace)
            for svc in services.items:
                key = f"Service/{svc.metadata.name}"
                state[key] = {
                    'type': svc.spec.type,
                    'ports': len(svc.spec.ports)
                }
        except ApiException as e:
            logger.error(f"Error getting cluster state: {e}")
            
        return state
        
    def _calculate_diff(self, git_state: Dict, cluster_state: Dict) -> List:
        """Calculate differences between Git and cluster"""
        changes = []
        
        # Resources to create (in Git but not in cluster)
        for resource, manifest in git_state.items():
            if resource not in cluster_state:
                changes.append({
                    'action': 'create',
                    'resource': resource,
                    'manifest': manifest
                })
            else:
                # Check for updates
                if self._resource_needs_update(manifest, cluster_state[resource]):
                    changes.append({
                        'action': 'update',
                        'resource': resource,
                        'manifest': manifest
                    })
                    
        # Resources to delete (in cluster but not in Git)
        for resource in cluster_state:
            if resource not in git_state:
                changes.append({
                    'action': 'delete',
                    'resource': resource
                })
                
        return changes
        
    def _resource_needs_update(self, manifest: Dict, cluster_resource: Dict) -> bool:
        """Determine if resource needs updating"""
        # Simplified comparison - in production, use strategic merge
        if manifest['kind'] == 'Deployment':
            git_replicas = manifest['spec'].get('replicas', 1)
            cluster_replicas = cluster_resource.get('replicas', 1)
            if git_replicas != cluster_replicas:
                return True
                
            git_image = manifest['spec']['template']['spec']['containers'][0]['image']
            cluster_image = cluster_resource.get('image', '')
            if git_image != cluster_image:
                return True
                
        return False
        
    async def _apply_changes(self, changes: List) -> bool:
        """Apply changes to cluster"""
        namespace = self.config['kubernetes']['namespace']
        
        try:
            for change in changes:
                action = change['action']
                resource = change['resource']
                
                logger.info(f"  {action.upper()}: {resource}")
                
                if action == 'create':
                    await self._create_resource(change['manifest'], namespace)
                elif action == 'update':
                    await self._update_resource(change['manifest'], namespace)
                elif action == 'delete':
                    await self._delete_resource(resource, namespace)
                    
            return True
        except Exception as e:
            logger.error(f"Error applying changes: {e}")
            return False
            
    async def _create_resource(self, manifest: Dict, namespace: str):
        """Create Kubernetes resource"""
        kind = manifest['kind']
        name = manifest['metadata']['name']
        
        if kind == 'Deployment':
            self.k8s_apps_v1.create_namespaced_deployment(
                namespace=namespace,
                body=manifest
            )
        elif kind == 'Service':
            self.k8s_core_v1.create_namespaced_service(
                namespace=namespace,
                body=manifest
            )
            
    async def _update_resource(self, manifest: Dict, namespace: str):
        """Update Kubernetes resource"""
        kind = manifest['kind']
        name = manifest['metadata']['name']
        
        if kind == 'Deployment':
            self.k8s_apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=manifest
            )
            
    async def _delete_resource(self, resource: str, namespace: str):
        """Delete Kubernetes resource"""
        kind, name = resource.split('/')
        
        if kind == 'Deployment':
            self.k8s_apps_v1.delete_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
    def _record_deployment(self, commit: str, changes: List, success: bool):
        """Record deployment in history"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'commit': commit[:8],
            'changes': len(changes),
            'success': success
        }
        self.deployment_history.append(record)
        
        # Keep last 100 deployments
        if len(self.deployment_history) > 100:
            self.deployment_history.pop(0)
            
    def get_status(self) -> Dict:
        """Get controller status"""
        return {
            'running': self.running,
            'last_sync_commit': self.last_sync_commit[:8] if self.last_sync_commit else None,
            'deployment_count': len(self.deployment_history),
            'recent_deployments': self.deployment_history[-5:]
        }
        
    async def stop(self):
        """Stop the controller"""
        logger.info("Stopping GitOps Controller...")
        self.running = False
