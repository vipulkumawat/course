"""
Ranking Engine with contextual relevance scoring
"""
import asyncio
import time
import math
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np

class RankingEngine:
    def __init__(self):
        self.ranking_weights = {
            "tfidf_score": 0.4,
            "temporal_relevance": 0.2,
            "severity_boost": 0.2,
            "service_authority": 0.1,
            "user_context": 0.1
        }
        
        self.service_authority_scores = {
            "auth-service": 0.9,
            "payment-service": 0.95,
            "user-service": 0.8,
            "notification-service": 0.7
        }
        
        self.level_severity_scores = {
            "ERROR": 1.0,
            "WARN": 0.7,
            "INFO": 0.4,
            "DEBUG": 0.2
        }
        
        self.ranking_stats = {
            "total_rankings": 0,
            "avg_ranking_time": 0,
            "context_adjustments": 0
        }
    
    async def initialize(self):
        """Initialize ranking engine"""
        print("Ranking engine initialized with contextual scoring")
    
    async def rank_results(self, search_results: Dict, query: Any, context: Optional[Dict] = None) -> List[Dict]:
        """Apply intelligent ranking to search results"""
        start_time = time.time()
        
        results = search_results.get("results", [])
        if not results:
            return []
        
        # Apply multi-factor ranking
        ranked_results = []
        for result in results:
            score_components = await self._calculate_score_components(result, query, context)
            final_score = await self._combine_scores(score_components)
            
            result_with_ranking = result.copy()
            result_with_ranking.update({
                "final_relevance_score": final_score,
                "score_components": score_components,
                "ranking_explanation": await self._generate_explanation(score_components)
            })
            
            ranked_results.append(result_with_ranking)
        
        # Sort by final relevance score
        ranked_results.sort(key=lambda x: x["final_relevance_score"], reverse=True)
        
        # Update ranking statistics
        ranking_time = (time.time() - start_time) * 1000
        self.ranking_stats["total_rankings"] += 1
        self.ranking_stats["avg_ranking_time"] = (
            (self.ranking_stats["avg_ranking_time"] * (self.ranking_stats["total_rankings"] - 1) + ranking_time) /
            self.ranking_stats["total_rankings"]
        )
        
        return ranked_results
    
    async def _calculate_score_components(self, result: Dict, query: Any, context: Optional[Dict]) -> Dict:
        """Calculate individual scoring components"""
        components = {}
        
        # TF-IDF base score
        components["tfidf_score"] = result.get("tfidf_score", 0.0)
        
        # Temporal relevance (recent logs score higher)
        components["temporal_relevance"] = await self._calculate_temporal_score(result)
        
        # Severity boost (errors are more important)
        components["severity_boost"] = self._calculate_severity_score(result)
        
        # Service authority (critical services score higher)
        components["service_authority"] = self._calculate_service_score(result)
        
        # User context (personalization)
        components["user_context"] = await self._calculate_context_score(result, context)
        
        return components
    
    async def _calculate_temporal_score(self, result: Dict) -> float:
        """Calculate temporal relevance score"""
        try:
            # Parse timestamp
            timestamp_str = result.get("timestamp", "")
            if not timestamp_str:
                return 0.5  # Default score for missing timestamp
            
            # For demo purposes, assume all logs are recent
            # In production, this would use actual timestamp parsing
            log_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            current_time = datetime.now(log_time.tzinfo)
            
            # Calculate age in hours
            age_hours = (current_time - log_time).total_seconds() / 3600
            
            # Exponential decay: recent logs score higher
            decay_factor = 0.1  # Adjust for faster/slower decay
            temporal_score = math.exp(-decay_factor * age_hours)
            
            return min(temporal_score, 1.0)
            
        except Exception:
            return 0.5  # Default score on parsing error
    
    def _calculate_severity_score(self, result: Dict) -> float:
        """Calculate severity-based score"""
        level = result.get("level", "INFO")
        return self.level_severity_scores.get(level, 0.4)
    
    def _calculate_service_score(self, result: Dict) -> float:
        """Calculate service authority score"""
        service = result.get("service", "unknown")
        return self.service_authority_scores.get(service, 0.5)
    
    async def _calculate_context_score(self, result: Dict, context: Optional[Dict]) -> float:
        """Calculate contextual relevance score"""
        if not context:
            return 0.5
        
        score = 0.5
        
        # Boost for user-specific context
        if context.get("user_focus"):
            user_terms = context["user_focus"].lower().split()
            result_text = result.get("message", "").lower()
            
            matching_terms = sum(1 for term in user_terms if term in result_text)
            if user_terms:
                score += 0.3 * (matching_terms / len(user_terms))
        
        # Boost for operational context
        if context.get("mode") == "incident":
            if result.get("level") == "ERROR":
                score += 0.4
                self.ranking_stats["context_adjustments"] += 1
        
        return min(score, 1.0)
    
    async def _combine_scores(self, components: Dict) -> float:
        """Combine individual scores using weighted sum"""
        final_score = 0.0
        
        for component, score in components.items():
            weight = self.ranking_weights.get(component, 0.0)
            final_score += weight * score
        
        return min(final_score, 1.0)
    
    async def _generate_explanation(self, components: Dict) -> str:
        """Generate human-readable ranking explanation"""
        explanations = []
        
        if components.get("tfidf_score", 0) > 0.7:
            explanations.append("High text relevance")
        
        if components.get("temporal_relevance", 0) > 0.8:
            explanations.append("Recent log entry")
        
        if components.get("severity_boost", 0) > 0.8:
            explanations.append("High severity level")
        
        if components.get("service_authority", 0) > 0.8:
            explanations.append("Critical service")
        
        if components.get("user_context", 0) > 0.7:
            explanations.append("Matches user context")
        
        if not explanations:
            explanations.append("Standard relevance")
        
        return "; ".join(explanations)
    
    async def get_stats(self) -> Dict:
        """Get ranking engine statistics"""
        return {
            "total_rankings": self.ranking_stats["total_rankings"],
            "avg_ranking_time_ms": round(self.ranking_stats["avg_ranking_time"], 2),
            "context_adjustments": self.ranking_stats["context_adjustments"],
            "ranking_weights": self.ranking_weights
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        print("Ranking engine cleanup completed")
