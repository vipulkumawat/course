"""Anomaly detection using Isolation Forest algorithm"""
from typing import Dict, Any, List, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest

class IsolationForestDetector:
    """Detect multi-dimensional anomalies using Isolation Forest"""
    
    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.models = {}  # Per-user models
        self.feature_names = []
    
    def train(self, user: str, historical_features: List[Dict[str, float]]):
        """Train isolation forest on historical data"""
        if len(historical_features) < 10:
            return  # Need minimum data
        
        # Extract feature matrix
        self.feature_names = list(historical_features[0].keys())
        X = np.array([
            [f.get(fname, 0.0) for fname in self.feature_names]
            for f in historical_features
        ])
        
        # Train model
        model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        model.fit(X)
        self.models[user] = model
    
    def detect(self, user: str, features: Dict[str, float]) -> Tuple[float, List[str]]:
        """
        Detect anomaly for user
        Returns: (anomaly_score, affected_features)
        """
        if user not in self.models:
            return 0.0, []
        
        model = self.models[user]
        
        # Prepare feature vector
        X = np.array([[features.get(fname, 0.0) for fname in self.feature_names]])
        
        # Get prediction (-1 for anomaly, 1 for normal)
        prediction = model.predict(X)[0]
        
        # Get anomaly score (lower is more anomalous)
        decision_score = model.decision_function(X)[0]
        
        # Normalize to 0-100 scale
        # decision_score ranges roughly from -0.5 to 0.5
        # Anomalies have negative scores
        if prediction == -1:
            score = min(100, abs(decision_score) * 100)
            
            # Identify most anomalous features
            anomalous_features = self._identify_anomalous_features(features)
            return score, anomalous_features
        
        return 0.0, []
    
    def _identify_anomalous_features(self, features: Dict[str, float]) -> List[str]:
        """Identify which features contribute most to anomaly"""
        # Simplified: return top 3 extreme features
        sorted_features = sorted(
            features.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        return [f[0] for f in sorted_features[:3]]
