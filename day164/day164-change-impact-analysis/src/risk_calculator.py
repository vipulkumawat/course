"""
Advanced risk calculation with historical data analysis
"""
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class HistoricalChange:
    service: str
    change_type: str
    predicted_risk: float
    actual_outcome: str  # 'success', 'minor_issue', 'major_incident'
    timestamp: datetime

class RiskCalculator:
    def __init__(self):
        self.historical_changes: List[HistoricalChange] = []
        self.risk_adjustments = {}
        
    def add_historical_data(self, change: HistoricalChange):
        """Track historical changes for learning"""
        self.historical_changes.append(change)
        self._update_risk_adjustments()
    
    def _update_risk_adjustments(self):
        """Learn from historical outcomes to adjust risk calculations"""
        if len(self.historical_changes) < 5:
            return
        
        # Analyze last 30 days
        cutoff = datetime.now() - timedelta(days=30)
        recent_changes = [c for c in self.historical_changes if c.timestamp > cutoff]
        
        # Calculate adjustment factors by change type
        for change_type in ['api_modification', 'schema_change', 'infrastructure']:
            relevant = [c for c in recent_changes if c.change_type == change_type]
            if not relevant:
                continue
            
            # Count actual incidents
            incidents = sum(1 for c in relevant if c.actual_outcome != 'success')
            incident_rate = incidents / len(relevant)
            
            # Adjust risk multiplier
            base_multiplier = 1.0
            if incident_rate > 0.3:  # More than 30% incident rate
                self.risk_adjustments[change_type] = base_multiplier * 1.3
            elif incident_rate < 0.1:  # Less than 10% incident rate
                self.risk_adjustments[change_type] = base_multiplier * 0.8
            else:
                self.risk_adjustments[change_type] = base_multiplier
    
    def get_adjusted_risk(self, base_risk: float, change_type: str) -> float:
        """Apply historical learning to risk score"""
        multiplier = self.risk_adjustments.get(change_type, 1.0)
        adjusted = base_risk * multiplier
        return round(min(adjusted, 100), 2)
    
    def get_risk_trend(self, service: str, days: int = 30) -> Dict:
        """Analyze risk trends for a specific service"""
        cutoff = datetime.now() - timedelta(days=days)
        service_changes = [
            c for c in self.historical_changes 
            if c.service == service and c.timestamp > cutoff
        ]
        
        if not service_changes:
            return {'trend': 'insufficient_data', 'changes': 0}
        
        incident_rate = sum(
            1 for c in service_changes if c.actual_outcome != 'success'
        ) / len(service_changes)
        
        return {
            'trend': 'increasing' if incident_rate > 0.2 else 'stable',
            'changes': len(service_changes),
            'incident_rate': round(incident_rate, 2),
            'recommendation': 'Increase review rigor' if incident_rate > 0.2 else 'Standard review process'
        }
