"""Statistical anomaly detection using Z-scores"""
from typing import Dict, Any, List, Tuple
import numpy as np

class ZScoreDetector:
    """Detect anomalies using statistical Z-scores"""
    
    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold
    
    def detect(self, features: Dict[str, float], baseline: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Detect anomalies in features
        Returns: (anomaly_score, list_of_anomalous_features)
        """
        if not baseline or not baseline.get('mean'):
            return 0.0, []
        
        anomalies = []
        z_scores = []
        
        for feature, value in features.items():
            mean = baseline['mean'].get(feature, value)
            std = baseline['std'].get(feature, 0.0)
            
            if std > 0:
                z_score = abs((value - mean) / std)
                z_scores.append(z_score)
                
                if z_score > self.threshold:
                    anomalies.append(f"{feature} (z={z_score:.2f})")
        
        # Aggregate score: percentage of anomalous features
        if z_scores:
            # Max Z-score normalized to 0-100
            # More sensitive: z-score of 6+ gives high risk, 10+ gives critical
            max_z = max(z_scores)
            # Scale: threshold (3.0) = 30, 6.0 = 60, 10.0 = 100
            if max_z >= 10.0:
                score = 100.0
            elif max_z >= 6.0:
                score = 60.0 + ((max_z - 6.0) / 4.0) * 40.0  # 60-100 range
            elif max_z >= 3.0:
                score = 30.0 + ((max_z - 3.0) / 3.0) * 30.0  # 30-60 range
            else:
                score = (max_z / self.threshold) * 30.0
            score = min(100, score)
            return score, anomalies
        
        return 0.0, []
    
    def get_details(self, features: Dict[str, float], baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed Z-score analysis"""
        details = {}
        
        for feature, value in features.items():
            mean = baseline['mean'].get(feature, value)
            std = baseline['std'].get(feature, 0.0)
            
            z_score = abs((value - mean) / std) if std > 0 else 0.0
            
            details[feature] = {
                'value': value,
                'mean': mean,
                'std': std,
                'z_score': z_score,
                'is_anomaly': z_score > self.threshold
            }
        
        return details
