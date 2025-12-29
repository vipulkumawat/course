import re
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ParsedIntent:
    intent: str
    confidence: float
    entities: Dict[str, any]
    raw_query: str

class IntentParser:
    """Parses user queries to extract intent"""
    
    def __init__(self):
        self.intent_patterns = {
            'search': [
                r'show\s+me', r'find', r'get', r'display', r'list', r'view'
            ],
            'count': [
                r'how\s+many', r'count', r'number\s+of', r'total'
            ],
            'aggregate': [
                r'sum', r'average', r'avg', r'max', r'min', r'group\s+by'
            ],
            'compare': [
                r'compare', r'difference', r'vs', r'versus', r'between'
            ],
            'investigate': [
                r'why', r'what\s+caused', r'reason', r'investigate'
            ]
        }
        
    def parse(self, query: str) -> ParsedIntent:
        """Parse user query and extract intent"""
        query_lower = query.lower().strip()
        
        # Classify intent
        intent, confidence = self._classify_intent(query_lower)
        
        # Extract entities (will be done by EntityExtractor)
        entities = {}
        
        return ParsedIntent(
            intent=intent,
            confidence=confidence,
            entities=entities,
            raw_query=query
        )
    
    def _classify_intent(self, query: str) -> tuple:
        """Classify query intent using pattern matching"""
        scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query):
                    score += 1
            scores[intent] = score
        
        if not any(scores.values()):
            return 'search', 0.5  # Default to search with low confidence
        
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]
        confidence = min(max_score / len(self.intent_patterns[max_intent]), 1.0)
        
        return max_intent, confidence
