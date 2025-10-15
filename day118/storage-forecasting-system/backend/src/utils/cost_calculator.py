from typing import Dict, List
from datetime import datetime, timedelta

class StorageCostCalculator:
    def __init__(self, 
                 primary_cost_per_gb=0.023,
                 replica_cost_per_gb=0.019,
                 archive_cost_per_gb=0.012):
        self.costs = {
            'primary': primary_cost_per_gb,
            'replica': replica_cost_per_gb,
            'archive': archive_cost_per_gb
        }
    
    def calculate_monthly_cost(self, usage_gb: float, storage_type: str = 'primary') -> float:
        """Calculate monthly storage cost"""
        cost_per_gb = self.costs.get(storage_type, self.costs['primary'])
        return usage_gb * cost_per_gb
    
    def calculate_forecast_costs(self, forecast_data: Dict, storage_type: str = 'primary') -> Dict:
        """Calculate costs for forecast period"""
        forecasted_usage = forecast_data['forecast']
        dates = forecast_data['dates']
        
        daily_costs = []
        monthly_costs = []
        
        for i, usage_bytes in enumerate(forecasted_usage):
            usage_gb = usage_bytes / (1024**3)
            daily_cost = self.calculate_monthly_cost(usage_gb, storage_type) / 30
            daily_costs.append(daily_cost)
            
            # Calculate monthly cost for this point
            monthly_cost = self.calculate_monthly_cost(usage_gb, storage_type)
            monthly_costs.append(monthly_cost)
        
        total_period_cost = sum(daily_costs)
        
        return {
            'daily_costs': daily_costs,
            'monthly_costs': monthly_costs,
            'total_period_cost': total_period_cost,
            'average_monthly_cost': sum(monthly_costs) / len(monthly_costs),
            'cost_trend': 'increasing' if monthly_costs[-1] > monthly_costs[0] else 'stable',
            'projected_annual_cost': monthly_costs[-1] * 12
        }
    
    def generate_cost_scenarios(self, current_usage_gb: float, growth_rates: List[float]) -> Dict:
        """Generate cost scenarios for different growth rates"""
        scenarios = {}
        
        for rate in growth_rates:
            scenario_name = f"{rate*100:.1f}%_growth"
            monthly_usage = []
            monthly_costs = []
            
            for month in range(12):  # 12 months projection
                projected_usage = current_usage_gb * (1 + rate) ** month
                monthly_usage.append(projected_usage)
                monthly_costs.append(self.calculate_monthly_cost(projected_usage))
            
            scenarios[scenario_name] = {
                'monthly_usage_gb': monthly_usage,
                'monthly_costs': monthly_costs,
                'total_annual_cost': sum(monthly_costs),
                'peak_usage_gb': max(monthly_usage),
                'growth_rate': rate
            }
        
        return scenarios
    
    def calculate_roi_for_optimization(self, current_cost: float, optimized_cost: float, 
                                     implementation_cost: float) -> Dict:
        """Calculate ROI for storage optimization initiatives"""
        annual_savings = (current_cost - optimized_cost) * 12
        roi_months = implementation_cost / (current_cost - optimized_cost) if current_cost > optimized_cost else float('inf')
        
        return {
            'annual_savings': annual_savings,
            'monthly_savings': current_cost - optimized_cost,
            'roi_months': roi_months,
            'roi_percentage': (annual_savings / implementation_cost) * 100 if implementation_cost > 0 else 0,
            'recommendation': 'implement' if roi_months < 12 else 'reconsider'
        }
