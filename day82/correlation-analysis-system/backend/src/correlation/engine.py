import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np
from scipy.stats import pearsonr, spearmanr
from collections import defaultdict
import structlog

logger = structlog.get_logger()

@dataclass
class CorrelationResult:
    event_a: Dict[str, Any]
    event_b: Dict[str, Any]
    correlation_type: str
    strength: float
    confidence: float
    timestamp: datetime
    window_seconds: int

class CorrelationEngine:
    def __init__(self, window_seconds: int = 30):
        self.window_seconds = window_seconds
        self.correlations = []
        self.patterns = defaultdict(list)
        self.running = False
        self.log_collector = None
        
    def set_log_collector(self, log_collector):
        """Set the log collector reference"""
        self.log_collector = log_collector
        
    async def start_processing(self):
        """Start correlation processing"""
        self.running = True
        logger.info("Starting correlation analysis engine")
        
        while self.running:
            await self._process_correlations()
            await asyncio.sleep(5)  # Process every 5 seconds
    
    async def _process_correlations(self):
        """Process correlations from collected events"""
        if not self.log_collector:
            return
            
        # Get recent events
        events = await self.log_collector.get_events(200)
        if len(events) < 2:
            return
        
        # Group events by time windows
        correlations = await self._find_temporal_correlations(events)
        
        # Store correlations
        self.correlations.extend(correlations)
        
        # Keep only recent correlations (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.correlations = [c for c in self.correlations if c.timestamp > cutoff_time]
        
        if correlations:
            logger.info(f"Found {len(correlations)} new correlations")
    
    async def _find_temporal_correlations(self, events: List) -> List[CorrelationResult]:
        """Find correlations within time windows"""
        correlations = []
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        for i, event_a in enumerate(sorted_events):
            for event_b in sorted_events[i+1:]:
                # Check if events are within time window
                time_diff = abs((event_b.timestamp - event_a.timestamp).total_seconds())
                
                if time_diff <= self.window_seconds:
                    correlation = await self._calculate_correlation(event_a, event_b, time_diff)
                    if correlation and correlation.strength > 0.3:  # Threshold for significance
                        correlations.append(correlation)
                else:
                    break  # Events are sorted, so we can break
        
        return correlations
    
    async def _calculate_correlation(self, event_a, event_b, time_diff: float) -> CorrelationResult:
        """Calculate correlation between two events"""
        
        # Correlation by correlation_id (same user session)
        if (hasattr(event_a, 'correlation_id') and hasattr(event_b, 'correlation_id') 
            and event_a.correlation_id == event_b.correlation_id and event_a.correlation_id):
            strength = 0.9 - (time_diff / self.window_seconds) * 0.4  # Decay with time
            return CorrelationResult(
                event_a=asdict(event_a),
                event_b=asdict(event_b),
                correlation_type="session_based",
                strength=strength,
                confidence=0.85,
                timestamp=datetime.now(),
                window_seconds=self.window_seconds
            )
        
        # Correlation by user_id
        if (hasattr(event_a, 'user_id') and hasattr(event_b, 'user_id') 
            and event_a.user_id == event_b.user_id and event_a.user_id):
            strength = 0.7 - (time_diff / self.window_seconds) * 0.3
            return CorrelationResult(
                event_a=asdict(event_a),
                event_b=asdict(event_b),
                correlation_type="user_based",
                strength=strength,
                confidence=0.75,
                timestamp=datetime.now(),
                window_seconds=self.window_seconds
            )
        
        # Error correlation (errors happening close in time)
        if (event_a.level == "ERROR" and event_b.level == "ERROR" 
            and event_a.source != event_b.source):
            strength = 0.6 - (time_diff / self.window_seconds) * 0.2
            return CorrelationResult(
                event_a=asdict(event_a),
                event_b=asdict(event_b),
                correlation_type="error_cascade",
                strength=strength,
                confidence=0.70,
                timestamp=datetime.now(),
                window_seconds=self.window_seconds
            )
        
        # Metric correlation (if both events have metrics)
        if (hasattr(event_a, 'metrics') and hasattr(event_b, 'metrics') 
            and event_a.metrics and event_b.metrics):
            
            # Find common metric keys
            common_metrics = set(event_a.metrics.keys()) & set(event_b.metrics.keys())
            if common_metrics:
                # Simple correlation based on metric similarity
                correlations = []
                for metric in common_metrics:
                    val_a = event_a.metrics[metric]
                    val_b = event_b.metrics[metric]
                    if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                        # Simple similarity measure
                        diff = abs(val_a - val_b)
                        max_val = max(abs(val_a), abs(val_b), 1)
                        similarity = 1 - (diff / max_val)
                        correlations.append(similarity)
                
                if correlations:
                    avg_correlation = np.mean(correlations)
                    if avg_correlation > 0.5:
                        strength = avg_correlation * 0.8 - (time_diff / self.window_seconds) * 0.2
                        return CorrelationResult(
                            event_a=asdict(event_a),
                            event_b=asdict(event_b),
                            correlation_type="metric_based",
                            strength=max(0, strength),
                            confidence=0.65,
                            timestamp=datetime.now(),
                            window_seconds=self.window_seconds
                        )
        
        return None
    
    async def get_correlations(self, limit: int = 100) -> List[CorrelationResult]:
        """Get recent correlations"""
        return sorted(self.correlations[-limit:], key=lambda c: c.timestamp, reverse=True)
    
    async def get_correlation_stats(self) -> Dict[str, Any]:
        """Get correlation statistics"""
        if not self.correlations:
            return {"total": 0, "types": {}, "avg_strength": 0}
        
        types = defaultdict(int)
        strengths = []
        
        for corr in self.correlations:
            types[corr.correlation_type] += 1
            strengths.append(corr.strength)
        
        return {
            "total": len(self.correlations),
            "types": dict(types),
            "avg_strength": np.mean(strengths) if strengths else 0,
            "max_strength": max(strengths) if strengths else 0,
            "recent_count": len([c for c in self.correlations 
                               if c.timestamp > datetime.now() - timedelta(minutes=5)])
        }
    
    def stop_processing(self):
        """Stop correlation processing"""
        self.running = False
        logger.info("Stopped correlation analysis engine")
