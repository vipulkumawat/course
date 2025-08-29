import asyncio
import logging
import yaml
from typing import Dict, List
from src.monitoring.metrics_collector import MetricsCollector
from src.policies.policy_engine import PolicyEngine
from src.orchestration.orchestrator import ContainerOrchestrator

class ScalingCoordinator:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.metrics_collector = MetricsCollector(self.config.get('monitoring', {}))
        self.policy_engine = PolicyEngine(self.config)
        self.orchestrator = ContainerOrchestrator(self.config.get('orchestration', {}))
        
        self.running = False
        self.evaluation_interval = self.config.get('monitoring', {}).get('evaluation_interval', 60)
        
    async def initialize(self):
        """Initialize the scaling system"""
        logging.info("Initializing automated scaling system...")
        
        # Register sample components for demonstration
        await self._register_demo_components()
        
        # Start metrics collection
        asyncio.create_task(self.metrics_collector.start_collection())
        
        logging.info("Scaling system initialized successfully")
    
    async def _register_demo_components(self):
        """Register demo components for testing"""
        demo_components = [
            ("log-processor-1", "log_processors"),
            ("log-processor-2", "log_processors"),
            ("log-collector-1", "collectors"),
            ("storage-node-1", "storage_nodes"),
            ("storage-node-2", "storage_nodes"),
        ]
        
        for component_id, component_type in demo_components:
            await self.metrics_collector.register_component(component_id, component_type)
            # Initialize container registry
            self.orchestrator._register_container(component_id, f"{component_id}-container-1")
    
    async def start_scaling_loop(self):
        """Start the main scaling evaluation loop"""
        self.running = True
        logging.info("Starting scaling evaluation loop...")
        
        while self.running:
            try:
                await self._evaluate_and_scale()
                await asyncio.sleep(self.evaluation_interval)
                
            except asyncio.CancelledError:
                logging.info("Scaling loop cancelled, shutting down...")
                break
            except Exception as e:
                logging.error(f"Error in scaling loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying
        
        logging.info("Scaling loop stopped")
    
    async def _evaluate_and_scale(self):
        """Evaluate metrics and execute scaling decisions"""
        try:
            # Get latest metrics
            metrics = self.metrics_collector.get_latest_metrics()
            
            if not metrics:
                logging.debug("No metrics available for evaluation")
                return
            
            # Update instance counts in metrics
            for component_id, component_metrics in metrics.items():
                current_instances = self.orchestrator.get_component_instance_count(component_id)
                component_metrics.instance_count = max(current_instances, 1)
            
            # Evaluate scaling policies
            scaling_decisions = self.policy_engine.evaluate_scaling_policies(metrics)
            
            if not scaling_decisions:
                logging.debug("No scaling actions required")
                return
            
            # Execute scaling decisions
            for decision in scaling_decisions:
                logging.info(f"Executing scaling decision: {decision.action.value} "
                            f"for {decision.component_id} "
                            f"({decision.current_instances} -> {decision.target_instances})")
                
                success = await self.orchestrator.execute_scaling_decision(decision)
                
                if success:
                    self.policy_engine.record_scaling_action(decision)
                    logging.info(f"Successfully executed scaling for {decision.component_id}")
                else:
                    logging.error(f"Failed to execute scaling for {decision.component_id}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.error(f"Error in scaling evaluation: {e}")

    def stop(self):
        """Stop the scaling system"""
        logging.info("Stopping scaling system...")
        self.running = False
        self.metrics_collector.stop_collection()
        logging.info("Scaling system stopped")
    
    def get_status(self) -> Dict:
        """Get current status of the scaling system"""
        metrics = self.metrics_collector.get_latest_metrics()
        scaling_history = self.policy_engine.scaling_history[-10:]  # Last 10 actions
        
        return {
            "running": self.running,
            "components": len(metrics),
            "recent_scaling_actions": len(scaling_history),
            "component_status": {
                component_id: {
                    "instance_count": self.orchestrator.get_component_instance_count(component_id),
                    "cpu_percent": metrics.get(component_id).cpu_percent if metrics.get(component_id) else 0,
                    "queue_depth": metrics.get(component_id).queue_depth if metrics.get(component_id) else 0
                }
                for component_id in metrics.keys()
            }
        }
