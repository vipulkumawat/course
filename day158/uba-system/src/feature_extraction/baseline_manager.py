"""Manage user behavioral baselines"""
from typing import Dict, Any, List
import numpy as np
from collections import defaultdict
import json

class BaselineManager:
    """Manage and update user baselines"""
    
    def __init__(self):
        self.baselines = defaultdict(lambda: {
            'mean': {},
            'std': {},
            'min': {},
            'max': {},
            'sample_count': 0
        })
    
    def update_baseline(self, user: str, features: Dict[str, float]):
        """Update baseline with new feature observation"""
        baseline = self.baselines[user]
        n = baseline['sample_count']
        
        for feature, value in features.items():
            if feature not in baseline['mean']:
                baseline['mean'][feature] = value
                baseline['std'][feature] = 0.0
                baseline['min'][feature] = value
                baseline['max'][feature] = value
            else:
                # Online mean and variance update
                old_mean = baseline['mean'][feature]
                baseline['mean'][feature] = old_mean + (value - old_mean) / (n + 1)
                
                # Welford's online algorithm for variance
                if n > 0:
                    old_std = baseline['std'][feature]
                    baseline['std'][feature] = np.sqrt(
                        (n * old_std**2 + (value - old_mean) * (value - baseline['mean'][feature])) / (n + 1)
                    )
                
                baseline['min'][feature] = min(baseline['min'][feature], value)
                baseline['max'][feature] = max(baseline['max'][feature], value)
        
        baseline['sample_count'] = n + 1
    
    def get_baseline(self, user: str) -> Dict[str, Any]:
        """Get baseline statistics for user"""
        return self.baselines.get(user, {})
    
    def is_trained(self, user: str, min_samples: int = 100) -> bool:
        """Check if baseline is sufficiently trained"""
        baseline = self.baselines.get(user)
        return baseline and baseline['sample_count'] >= min_samples
    
    def save(self, filepath: str):
        """Save baselines to file"""
        with open(filepath, 'w') as f:
            json.dump(dict(self.baselines), f, indent=2)
    
    def load(self, filepath: str):
        """Load baselines from file"""
        try:
            with open(filepath, 'r') as f:
                loaded = json.load(f)
                self.baselines = defaultdict(lambda: {
                    'mean': {}, 'std': {}, 'min': {}, 'max': {}, 'sample_count': 0
                }, loaded)
        except FileNotFoundError:
            pass
