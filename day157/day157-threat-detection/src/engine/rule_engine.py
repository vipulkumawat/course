import asyncio
from typing import List, Dict, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import uuid
from src.models import DetectionRule, LogEntry, ThreatDetection, SeverityLevel
from src.engine.pattern_matcher import PatternMatcher
import structlog

logger = structlog.get_logger()

class RuleEngine:
    def __init__(self, rules: List[DetectionRule]):
        self.rules = rules
        self.pattern_matcher = PatternMatcher()
        self.pattern_matcher.compile_rules(rules)
        
        # State tracking for stateful rules
        self.failed_login_tracker: Dict[str, deque] = defaultdict(deque)
        self.distributed_attacks: Dict[str, List] = defaultdict(list)
        
        # Performance metrics
        self.total_logs_processed = 0
        self.total_detections = 0
        self.detections_by_severity = defaultdict(int)
        
    async def evaluate(self, log_entry: LogEntry) -> List[ThreatDetection]:
        """Evaluate log entry against all rules"""
        self.total_logs_processed += 1
        detections = []
        
        # Sort rules by severity (process critical first)
        sorted_rules = sorted(
            self.rules,
            key=lambda r: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(r.severity),
            reverse=True
        )
        
        for rule in sorted_rules:
            detection = await self._evaluate_rule(log_entry, rule)
            if detection:
                detections.append(detection)
                self.total_detections += 1
                self.detections_by_severity[detection.severity] += 1
                
                # Short-circuit on critical detections
                if detection.severity == SeverityLevel.CRITICAL:
                    break
        
        return detections
    
    async def _evaluate_rule(
        self,
        log_entry: LogEntry,
        rule: DetectionRule
    ) -> Optional[ThreatDetection]:
        """Evaluate a single rule"""
        
        # Pattern matching
        match_result = self.pattern_matcher.match(log_entry, rule)
        if not match_result:
            return None
        
        matched, matched_pattern = match_result
        
        # Stateful evaluation for certain rule types
        if rule.threshold and rule.time_window:
            if not self._check_threshold(log_entry, rule):
                return None
        
        # Calculate confidence based on context
        confidence = self._calculate_confidence(log_entry, rule, matched_pattern)
        
        # Create detection
        detection = ThreatDetection(
            detection_id=str(uuid.uuid4()),
            rule_name=rule.name,
            severity=rule.severity,
            category=rule.category,
            log_entry=log_entry,
            matched_pattern=matched_pattern,
            confidence=confidence,
            action_taken=rule.action,
            context=self._build_context(log_entry, rule)
        )
        
        logger.warning(
            "threat_detected",
            detection_id=detection.detection_id,
            rule=rule.name,
            severity=rule.severity,
            source_ip=log_entry.source_ip
        )
        
        return detection
    
    def _check_threshold(self, log_entry: LogEntry, rule: DetectionRule) -> bool:
        """Check if threshold exceeded for stateful rules"""
        key = log_entry.source_ip if not rule.distributed else log_entry.user_id
        if not key:
            return False
        
        now = datetime.now()
        tracker = self.failed_login_tracker[key]
        
        # Clean old entries
        while tracker and (now - tracker[0]) > timedelta(seconds=rule.time_window):
            tracker.popleft()
        
        tracker.append(now)
        
        return len(tracker) >= rule.threshold
    
    def _calculate_confidence(
        self,
        log_entry: LogEntry,
        rule: DetectionRule,
        matched_pattern: str
    ) -> float:
        """Calculate detection confidence"""
        confidence = 0.7  # Base confidence
        
        # Increase confidence for known attack IPs
        if self._is_known_attacker(log_entry.source_ip):
            confidence += 0.2
        
        # Increase confidence for multiple pattern matches
        if len(matched_pattern) > 20:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _is_known_attacker(self, ip: str) -> bool:
        """Check if IP is in known attacker database"""
        # Simplified check - in production, query threat intelligence DB
        return ip.startswith("192.168.") or ip.startswith("10.")
    
    def _build_context(self, log_entry: LogEntry, rule: DetectionRule) -> Dict:
        """Build context information for detection"""
        return {
            "endpoint": log_entry.endpoint,
            "method": log_entry.method,
            "status_code": log_entry.status_code,
            "user_agent": log_entry.user_agent,
            "rule_category": rule.category,
            "historical_attacks": len(self.failed_login_tracker.get(log_entry.source_ip, []))
        }
    
    def get_stats(self) -> Dict:
        """Get engine statistics"""
        return {
            "total_logs_processed": self.total_logs_processed,
            "total_detections": self.total_detections,
            "detections_by_severity": dict(self.detections_by_severity),
            "detection_rate": (
                self.total_detections / self.total_logs_processed
                if self.total_logs_processed > 0 else 0
            ),
            **self.pattern_matcher.get_stats()
        }
