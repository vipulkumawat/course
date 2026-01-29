"""Extract behavioral features from parsed logs"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import numpy as np

class FeatureEngine:
    """Extract user behavioral features"""
    
    def __init__(self):
        self.user_history = defaultdict(list)
        
    def add_event(self, user: str, event: Dict[str, Any]):
        """Add event to user history"""
        self.user_history[user].append(event)
        
        # Keep only last 30 days
        cutoff = datetime.now() - timedelta(days=30)
        self.user_history[user] = [
            e for e in self.user_history[user]
            if datetime.fromisoformat(e['timestamp']) > cutoff
        ]
    
    def extract_features(self, user: str, current_event: Dict[str, Any]) -> Dict[str, float]:
        """Extract behavioral feature vector"""
        history = self.user_history.get(user, [])
        
        features = {
            'login_frequency': self._login_frequency(history),
            'access_count': self._access_count(history),
            'data_volume': self._data_volume(history),
            'failed_attempts': self._failed_attempts(history),
            'session_duration': self._session_duration(current_event, history),
            'geographic_entropy': self._geographic_entropy(history),
            'time_of_day_score': self._time_of_day_score(current_event),
            'resource_diversity': self._resource_diversity(history),
            'hourly_access_rate': self._hourly_access_rate(history),
            'weekend_activity': self._weekend_activity(history)
        }
        
        return features
    
    def _login_frequency(self, history: List[Dict]) -> float:
        """Count logins per day"""
        logins = [e for e in history if e['event_type'] == 'login']
        if not logins:
            return 0.0
        
        days = (datetime.now() - datetime.fromisoformat(logins[0]['timestamp'])).days + 1
        return len(logins) / max(days, 1)
    
    def _access_count(self, history: List[Dict]) -> float:
        """Count resource accesses per day"""
        accesses = [e for e in history if e['event_type'] == 'access']
        if not accesses:
            return 0.0
        
        days = (datetime.now() - datetime.fromisoformat(accesses[0]['timestamp'])).days + 1
        return len(accesses) / max(days, 1)
    
    def _data_volume(self, history: List[Dict]) -> float:
        """Average bytes downloaded per day"""
        downloads = [e for e in history if e['event_type'] == 'download']
        if not downloads:
            return 0.0
        
        total_bytes = sum(e['details'].get('bytes', 0) for e in downloads)
        days = (datetime.now() - datetime.fromisoformat(downloads[0]['timestamp'])).days + 1
        return total_bytes / max(days, 1)
    
    def _failed_attempts(self, history: List[Dict]) -> float:
        """Count failed login attempts"""
        failed = [e for e in history if e['event_type'] == 'failed_login']
        return float(len(failed))
    
    def _session_duration(self, current_event: Dict, history: List[Dict]) -> float:
        """Estimate session duration in minutes"""
        if current_event.get('session_id'):
            session_events = [
                e for e in history 
                if e.get('session_id') == current_event['session_id']
            ]
            if len(session_events) >= 2:
                start = datetime.fromisoformat(session_events[0]['timestamp'])
                end = datetime.fromisoformat(session_events[-1]['timestamp'])
                return (end - start).total_seconds() / 60
        return 30.0  # Default 30 minutes
    
    def _geographic_entropy(self, history: List[Dict]) -> float:
        """Calculate geographic diversity (entropy)"""
        ips = [e.get('ip_address') for e in history if e.get('ip_address')]
        if not ips:
            return 0.0
        
        # Simple entropy calculation
        ip_counts = Counter(ips)
        total = len(ips)
        entropy = -sum((count/total) * np.log2(count/total) for count in ip_counts.values())
        return entropy
    
    def _time_of_day_score(self, event: Dict) -> float:
        """Score based on time of day (0-23 hours)"""
        timestamp = datetime.fromisoformat(event['timestamp'])
        hour = timestamp.hour
        
        # Normal business hours (9-17) score lower
        if 9 <= hour <= 17:
            return 10.0
        # Evening (18-22) slightly higher
        elif 18 <= hour <= 22:
            return 30.0
        # Late night (23-5) high score
        else:
            return 80.0
    
    def _resource_diversity(self, history: List[Dict]) -> float:
        """Count unique resources accessed"""
        resources = set()
        for e in history:
            if e['event_type'] == 'access':
                resource = e['details'].get('resource')
                if resource:
                    resources.add(resource)
        return float(len(resources))
    
    def _hourly_access_rate(self, history: List[Dict]) -> float:
        """Accesses per hour (recent 24 hours)"""
        cutoff = datetime.now() - timedelta(hours=24)
        recent = [
            e for e in history
            if datetime.fromisoformat(e['timestamp']) > cutoff
        ]
        return float(len(recent))
    
    def _weekend_activity(self, history: List[Dict]) -> float:
        """Percentage of activity on weekends"""
        if not history:
            return 0.0
        
        weekend_events = sum(
            1 for e in history
            if datetime.fromisoformat(e['timestamp']).weekday() >= 5
        )
        return (weekend_events / len(history)) * 100
