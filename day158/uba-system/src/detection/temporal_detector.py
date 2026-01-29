"""Temporal pattern anomaly detection"""
from typing import Dict, Any, List, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np

class TemporalDetector:
    """Detect time-based behavioral anomalies"""
    
    def __init__(self):
        self.temporal_patterns = defaultdict(lambda: {
            'hourly_counts': defaultdict(int),
            'daily_counts': defaultdict(int),
            'weekday_counts': defaultdict(int)
        })
    
    def learn_pattern(self, user: str, timestamp: str):
        """Learn user's temporal access patterns"""
        dt = datetime.fromisoformat(timestamp)
        patterns = self.temporal_patterns[user]
        
        patterns['hourly_counts'][dt.hour] += 1
        patterns['daily_counts'][dt.day] += 1
        patterns['weekday_counts'][dt.weekday()] += 1
    
    def detect(self, user: str, timestamp: str) -> Tuple[float, List[str]]:
        """
        Detect temporal anomalies
        Returns: (anomaly_score, reasons)
        """
        if user not in self.temporal_patterns:
            return 0.0, []
        
        dt = datetime.fromisoformat(timestamp)
        patterns = self.temporal_patterns[user]
        
        anomalies = []
        scores = []
        
        # Check hour anomaly
        hour_score = self._check_hour_anomaly(dt.hour, patterns['hourly_counts'])
        if hour_score > 50:
            anomalies.append(f"Unusual hour: {dt.hour}:00")
            scores.append(hour_score)
        
        # Check weekday anomaly
        weekday_score = self._check_weekday_anomaly(dt.weekday(), patterns['weekday_counts'])
        if weekday_score > 50:
            day_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][dt.weekday()]
            anomalies.append(f"Unusual day: {day_name}")
            scores.append(weekday_score)
        
        # Return max score
        final_score = max(scores) if scores else 0.0
        return final_score, anomalies
    
    def _check_hour_anomaly(self, hour: int, hourly_counts: Dict[int, int]) -> float:
        """Check if hour is anomalous"""
        if not hourly_counts:
            return 0.0
        
        count = hourly_counts.get(hour, 0)
        avg_count = np.mean(list(hourly_counts.values()))
        
        # If this hour has never been seen before
        if count == 0:
            return 90.0
        
        # If significantly below average
        if count < avg_count * 0.1:
            return 70.0
        
        return 0.0
    
    def _check_weekday_anomaly(self, weekday: int, weekday_counts: Dict[int, int]) -> float:
        """Check if weekday is anomalous"""
        if not weekday_counts:
            return 0.0
        
        count = weekday_counts.get(weekday, 0)
        avg_count = np.mean(list(weekday_counts.values()))
        
        # Weekend vs weekday pattern
        is_weekend = weekday >= 5
        weekend_avg = np.mean([weekday_counts.get(5, 0), weekday_counts.get(6, 0)])
        weekday_avg = np.mean([weekday_counts.get(i, 0) for i in range(5)])
        
        if count == 0:
            return 80.0
        
        if is_weekend and weekday_avg > 0 and weekend_avg < weekday_avg * 0.1:
            return 70.0
        
        return 0.0
