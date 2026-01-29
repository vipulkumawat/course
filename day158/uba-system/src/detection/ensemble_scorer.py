"""Ensemble scoring combining multiple detectors"""
from typing import Dict, Any, List, Tuple

class EnsembleScorer:
    """Combine multiple detector outputs into final risk score"""
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            'zscore': 0.4,
            'isolation_forest': 0.4,
            'temporal': 0.2
        }
    
    def compute_score(self, detector_scores: Dict[str, Tuple[float, List[str]]]) -> Dict[str, Any]:
        """
        Combine detector scores
        detector_scores: {'detector_name': (score, anomalies)}
        """
        weighted_score = 0.0
        all_anomalies = []
        details = {}
        
        for detector, (score, anomalies) in detector_scores.items():
            weight = self.weights.get(detector, 0.33)
            weighted_score += score * weight
            all_anomalies.extend(anomalies)
            
            details[detector] = {
                'score': score,
                'weight': weight,
                'anomalies': anomalies
            }
        
        # Determine risk level
        risk_level = self._classify_risk(weighted_score)
        
        return {
            'final_score': round(weighted_score, 2),
            'risk_level': risk_level,
            'anomalies': all_anomalies,
            'detector_details': details
        }
    
    def _classify_risk(self, score: float) -> str:
        """Classify risk level based on score"""
        if score >= 80:
            return 'critical'
        elif score >= 60:
            return 'high'
        elif score >= 40:
            return 'medium'
        elif score >= 20:
            return 'low'
        return 'normal'
