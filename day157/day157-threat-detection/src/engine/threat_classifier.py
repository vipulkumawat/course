from typing import List, Dict
from collections import defaultdict
from src.models import ThreatDetection, SeverityLevel
import structlog

logger = structlog.get_logger()

class ThreatClassifier:
    def __init__(self):
        self.threat_scores: Dict[str, float] = {
            SeverityLevel.LOW: 1.0,
            SeverityLevel.MEDIUM: 2.5,
            SeverityLevel.HIGH: 5.0,
            SeverityLevel.CRITICAL: 10.0
        }
        self.classification_history = defaultdict(list)
    
    def classify_threat_level(self, detections: List[ThreatDetection]) -> Dict:
        """Classify overall threat level from multiple detections"""
        if not detections:
            return {
                "threat_level": "NONE",
                "risk_score": 0.0,
                "recommended_action": "monitor"
            }
        
        # Calculate cumulative risk score
        risk_score = sum(
            self.threat_scores[d.severity] * d.confidence
            for d in detections
        )
        
        # Determine threat level
        if risk_score >= 20:
            threat_level = "CRITICAL"
            recommended_action = "immediate_response"
        elif risk_score >= 10:
            threat_level = "HIGH"
            recommended_action = "investigate_urgently"
        elif risk_score >= 5:
            threat_level = "MEDIUM"
            recommended_action = "investigate"
        else:
            threat_level = "LOW"
            recommended_action = "log_and_monitor"
        
        classification = {
            "threat_level": threat_level,
            "risk_score": risk_score,
            "recommended_action": recommended_action,
            "detection_count": len(detections),
            "severity_breakdown": self._get_severity_breakdown(detections),
            "category_breakdown": self._get_category_breakdown(detections)
        }
        
        # Track classification
        self.classification_history[threat_level].append(classification)
        
        return classification
    
    def _get_severity_breakdown(self, detections: List[ThreatDetection]) -> Dict:
        """Get count of detections by severity"""
        breakdown = defaultdict(int)
        for detection in detections:
            breakdown[detection.severity] += 1
        return dict(breakdown)
    
    def _get_category_breakdown(self, detections: List[ThreatDetection]) -> Dict:
        """Get count of detections by category"""
        breakdown = defaultdict(int)
        for detection in detections:
            breakdown[detection.category] += 1
        return dict(breakdown)
    
    def get_classification_stats(self) -> Dict:
        """Get classification statistics"""
        return {
            "total_classifications": sum(
                len(v) for v in self.classification_history.values()
            ),
            "by_threat_level": {
                k: len(v) for k, v in self.classification_history.items()
            }
        }
