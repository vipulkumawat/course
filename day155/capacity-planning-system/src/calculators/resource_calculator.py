"""
Resource Calculator for Capacity Planning
Converts predicted log volumes to infrastructure requirements
"""

import yaml
import numpy as np
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceCalculator:
    """Calculates infrastructure requirements from predicted load"""
    
    def __init__(self, cluster_config_path: str = 'config/cluster.yaml',
                 planning_config_path: str = 'config/planning_config.yaml'):
        
        with open(cluster_config_path, 'r') as f:
            self.cluster_config = yaml.safe_load(f)
        
        with open(planning_config_path, 'r') as f:
            planning_config = yaml.safe_load(f)
            self.resource_profile = planning_config['resource_calculation']['cluster_profile']
            self.cost_per_node = planning_config['resource_calculation']['cost_per_node_monthly']
    
    def calculate_requirements(self, predicted_logs_per_sec: float,
                               buffer_factor: float = 1.2) -> Dict:
        """
        Calculate infrastructure requirements for predicted load
        buffer_factor: Headroom for spikes (1.2 = 20% buffer)
        """
        # Apply buffer for safety margin
        effective_load = predicted_logs_per_sec * buffer_factor
        
        # Calculate required nodes
        logs_per_node = self.resource_profile['logs_per_second_per_node']
        required_nodes = int(np.ceil(effective_load / logs_per_node))
        
        # Calculate resource totals
        cpu_per_node = self.resource_profile['cpu_cores_per_node']
        memory_per_node = self.resource_profile['memory_gb_per_node']
        disk_per_node = self.resource_profile['disk_gb_per_node']
        
        return {
            'predicted_load_logs_per_sec': float(predicted_logs_per_sec),
            'effective_load_with_buffer': float(effective_load),
            'buffer_percentage': (buffer_factor - 1) * 100,
            'nodes': {
                'current': self.cluster_config['current_nodes'],
                'required': required_nodes,
                'to_add': max(0, required_nodes - self.cluster_config['current_nodes']),
                'capacity_utilization': float(effective_load / (required_nodes * logs_per_node))
            },
            'resources': {
                'total_cpu_cores': required_nodes * cpu_per_node,
                'total_memory_gb': required_nodes * memory_per_node,
                'total_disk_gb': required_nodes * disk_per_node
            },
            'cost': {
                'monthly_usd': required_nodes * self.cost_per_node,
                'annual_usd': required_nodes * self.cost_per_node * 12,
                'additional_monthly_usd': max(0, required_nodes - self.cluster_config['current_nodes']) * self.cost_per_node
            }
        }
    
    def calculate_timeline_requirements(self, forecast: Dict) -> List[Dict]:
        """Calculate requirements for each day in forecast"""
        predictions = forecast['predictions']
        days = len(predictions) // 24
        
        timeline = []
        for day in range(days):
            # Peak load for the day
            day_predictions = predictions[day*24:(day+1)*24]
            peak_load = max(day_predictions)
            
            requirements = self.calculate_requirements(peak_load)
            requirements['day'] = day + 1
            requirements['date_offset'] = f"+{day+1}d"
            
            timeline.append(requirements)
        
        return timeline
    
    def generate_capacity_plan(self, forecast: Dict, 
                               target_utilization: float = 0.75) -> Dict:
        """
        Generate comprehensive capacity plan with scaling recommendations
        target_utilization: Desired capacity utilization (0.75 = 75%)
        """
        timeline = self.calculate_timeline_requirements(forecast)
        
        # Find when capacity needs to scale
        current_nodes = self.cluster_config['current_nodes']
        logs_per_node = self.resource_profile['logs_per_second_per_node']
        current_capacity = current_nodes * logs_per_node
        
        scale_events = []
        for req in timeline:
            if req['nodes']['required'] > current_nodes:
                scale_events.append({
                    'day': req['day'],
                    'reason': 'capacity_increase',
                    'action': f"Add {req['nodes']['to_add']} nodes",
                    'predicted_load': req['predicted_load_logs_per_sec'],
                    'utilization': req['nodes']['capacity_utilization']
                })
                current_nodes = req['nodes']['required']
        
        # Summary statistics
        max_requirement = max(timeline, key=lambda x: x['nodes']['required'])
        total_additional_cost = sum(req['cost']['additional_monthly_usd'] for req in timeline) / len(timeline)
        
        return {
            'forecast_period_days': len(timeline),
            'current_capacity': {
                'nodes': self.cluster_config['current_nodes'],
                'logs_per_second': current_capacity
            },
            'peak_requirement': {
                'day': max_requirement['day'],
                'nodes': max_requirement['nodes']['required'],
                'logs_per_second': max_requirement['predicted_load_logs_per_sec']
            },
            'scale_events': scale_events,
            'cost_projection': {
                'current_monthly_usd': self.cluster_config['current_nodes'] * self.cost_per_node,
                'projected_monthly_usd': max_requirement['cost']['monthly_usd'],
                'additional_monthly_usd': total_additional_cost,
                'annual_additional_usd': total_additional_cost * 12
            },
            'timeline': timeline
        }


if __name__ == '__main__':
    import argparse
    from analyzers.forecasting_engine import ForecastingEngine
    
    parser = argparse.ArgumentParser(description='Calculate resource requirements')
    parser.add_argument('--scenario', choices=['current', 'peak', 'plan'],
                       default='plan', help='Scenario to calculate')
    
    args = parser.parse_args()
    
    calculator = ResourceCalculator()
    
    if args.scenario == 'current':
        # Current capacity
        current_load = 40000  # Example current load
        req = calculator.calculate_requirements(current_load)
        print(f"\n💻 Current Capacity Requirements:")
        print(f"   Nodes: {req['nodes']['current']} → {req['nodes']['required']} required")
        print(f"   Utilization: {req['nodes']['capacity_utilization']:.1%}")
        
    elif args.scenario == 'peak':
        # Peak scenario
        peak_load = 75000  # Example peak
        req = calculator.calculate_requirements(peak_load)
        print(f"\n📈 Peak Load Requirements:")
        print(f"   Predicted: {req['predicted_load_logs_per_sec']:.0f} logs/sec")
        print(f"   Nodes needed: {req['nodes']['required']}")
        print(f"   To add: {req['nodes']['to_add']}")
        print(f"   Cost: ${req['cost']['monthly_usd']}/month")
        
    else:
        # Full capacity plan
        engine = ForecastingEngine()
        engine.load_historical_data('data/historical.csv')
        forecast = engine.predict(days=30)
        
        plan = calculator.generate_capacity_plan(forecast)
        
        print(f"\n📋 30-Day Capacity Plan:")
        print(f"   Current: {plan['current_capacity']['nodes']} nodes")
        print(f"   Peak need: {plan['peak_requirement']['nodes']} nodes (day {plan['peak_requirement']['day']})")
        print(f"   Scale events: {len(plan['scale_events'])}")
        print(f"   Additional cost: ${plan['cost_projection']['additional_monthly_usd']:.2f}/month")
