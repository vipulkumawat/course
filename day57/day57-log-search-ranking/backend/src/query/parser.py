"""
Query parser for natural language search queries
"""
import re
from typing import Dict, List
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

class QueryParser:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Domain-specific synonyms for log search
        self.synonyms = {
            "error": ["fail", "exception", "bug", "issue"],
            "slow": ["timeout", "latency", "delay", "performance"],
            "user": ["customer", "account", "profile"],
            "payment": ["transaction", "billing", "charge"],
            "auth": ["authentication", "login", "access", "permission"]
        }
    
    async def parse(self, query_text: str) -> Dict:
        """Parse natural language query into structured format"""
        original_query = query_text.strip()
        
        # Extract structured elements
        parsed = {
            "original": original_query,
            "normalized": await self._normalize_query(original_query),
            "expanded_query": await self._expand_query(original_query),
            "terms": await self._extract_terms(original_query),
            "filters": await self._extract_filters(original_query),
            "intent": await self._detect_intent(original_query)
        }
        
        return parsed
    
    async def _normalize_query(self, query: str) -> str:
        """Normalize query text"""
        # Convert to lowercase
        query = query.lower()
        
        # Remove special characters except spaces and quotes
        query = re.sub(r'[^\w\s".-]', ' ', query)
        
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    async def _expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms"""
        normalized = await self._normalize_query(query)
        words = normalized.split()
        
        expanded_words = []
        for word in words:
            expanded_words.append(word)
            
            # Add synonyms
            for key, synonyms in self.synonyms.items():
                if word in [key] + synonyms:
                    expanded_words.extend([s for s in synonyms if s != word])
        
        return " ".join(expanded_words)
    
    async def _extract_terms(self, query: str) -> List[str]:
        """Extract important terms from query"""
        normalized = await self._normalize_query(query)
        tokens = word_tokenize(normalized)
        
        # Remove stop words and lemmatize
        terms = []
        for token in tokens:
            if token not in self.stop_words and len(token) > 2:
                lemmatized = self.lemmatizer.lemmatize(token)
                terms.append(lemmatized)
        
        return terms
    
    async def _extract_filters(self, query: str) -> Dict:
        """Extract filters from query (e.g., level:error, service:auth)"""
        filters = {}
        
        # Look for filter patterns like "level:error"
        filter_pattern = r'(\w+):(\w+)'
        matches = re.findall(filter_pattern, query)
        
        for field, value in matches:
            filters[field] = value
        
        # Look for common implicit filters
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['error', 'exception', 'fail']):
            filters['implied_level'] = 'error'
        
        if any(word in query_lower for word in ['warn', 'warning']):
            filters['implied_level'] = 'warn'
        
        return filters
    
    async def _detect_intent(self, query: str) -> str:
        """Detect user intent from query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['error', 'exception', 'fail', 'problem']):
            return 'troubleshooting'
        
        if any(word in query_lower for word in ['performance', 'slow', 'timeout', 'latency']):
            return 'performance_analysis'
        
        if any(word in query_lower for word in ['user', 'customer', 'account']):
            return 'user_activity'
        
        if any(word in query_lower for word in ['payment', 'transaction', 'billing']):
            return 'payment_analysis'
        
        return 'general_search'
