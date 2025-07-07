"""
Search Engine with TF-IDF based relevance scoring
"""
import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import math
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from query.parser import QueryParser
from utils.text_processing import TextProcessor

class SearchEngine:
    def __init__(self):
        self.query_parser = QueryParser()
        self.text_processor = TextProcessor()
        self.tfidf_vectorizer = None
        self.document_vectors = None
        self.document_index = {}
        self.term_frequencies = defaultdict(Counter)
        self.document_frequencies = defaultdict(int)
        self.total_documents = 0
        
        # Search statistics
        self.search_stats = {
            "total_searches": 0,
            "avg_response_time": 0,
            "popular_terms": Counter()
        }
    
    async def initialize(self):
        """Initialize search engine with sample log data"""
        # Load sample log data for demonstration
        sample_logs = await self._generate_sample_logs()
        await self._build_index(sample_logs)
        
        print("Search engine initialized with TF-IDF indexing")
    
    async def _generate_sample_logs(self) -> List[Dict]:
        """Generate realistic sample log data"""
        sample_logs = [
            {
                "id": f"log_{i}",
                "timestamp": f"2025-06-16T{10+i%12:02d}:30:00Z",
                "level": ["INFO", "WARN", "ERROR", "DEBUG"][i % 4],
                "service": ["auth-service", "payment-service", "user-service", "notification-service"][i % 4],
                "message": msg,
                "metadata": {"request_id": f"req_{i}", "user_id": f"user_{i%100}"}
            }
            for i, msg in enumerate([
                "User authentication successful for premium account",
                "Payment processing timeout occurred during checkout",
                "Database connection pool exhausted, scaling up",
                "Cache miss for user profile data, fetching from database",
                "API rate limit exceeded for external service integration",
                "Successful user registration with email verification",
                "Payment gateway returned invalid response format",
                "Authentication token expired, requesting refresh",
                "Database query optimization reduced response time by 40%",
                "Memory usage approaching threshold, triggering garbage collection",
                "User session timeout after 30 minutes of inactivity",
                "Payment fraud detection triggered for suspicious transaction",
                "API response time degraded due to downstream service latency",
                "Successful database backup completed in 45 seconds",
                "Authentication service temporarily unavailable during deployment",
                "Payment processing completed successfully with transaction fees",
                "User notification delivery failed due to invalid email address",
                "Database index rebuild improved query performance significantly",
                "Cache warming completed for frequently accessed user data",
                "Payment service health check passed all validation tests"
            ])
        ]
        return sample_logs
    
    async def _build_index(self, logs: List[Dict]):
        """Build TF-IDF index from log documents"""
        # Extract text content for indexing
        documents = []
        for log in logs:
            # Combine searchable fields
            text_content = f"{log['message']} {log['service']} {log['level']}"
            documents.append(text_content)
            self.document_index[len(documents) - 1] = log
        
        # Build TF-IDF vectors
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8
        )
        
        self.document_vectors = self.tfidf_vectorizer.fit_transform(documents)
        self.total_documents = len(documents)
        
        print(f"Built TF-IDF index for {self.total_documents} documents")
    
    async def parse_query(self, query_text: str) -> Dict:
        """Parse and expand search query"""
        return await self.query_parser.parse(query_text)
    
    async def search(self, parsed_query: Dict) -> Dict:
        """Execute search with TF-IDF scoring"""
        start_time = time.time()
        
        query_text = parsed_query.get('expanded_query', parsed_query['original'])
        
        # Vectorize query using same TF-IDF model
        query_vector = self.tfidf_vectorizer.transform([query_text])
        
        # Calculate cosine similarity with all documents
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:50]  # Top 50 results
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include non-zero similarities
                doc = self.document_index[idx].copy()
                doc['relevance_score'] = float(similarities[idx])
                doc['tfidf_score'] = float(similarities[idx])
                results.append(doc)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Update search statistics
        self.search_stats["total_searches"] += 1
        self.search_stats["avg_response_time"] = (
            (self.search_stats["avg_response_time"] * (self.search_stats["total_searches"] - 1) + execution_time) /
            self.search_stats["total_searches"]
        )
        
        # Track popular search terms
        terms = query_text.lower().split()
        for term in terms:
            self.search_stats["popular_terms"][term] += 1
        
        return {
            "results": results,
            "total_hits": len(results),
            "execution_time": execution_time,
            "query_info": parsed_query
        }
    
    async def get_suggestions(self, partial_query: str) -> List[str]:
        """Generate search suggestions based on popular terms"""
        suggestions = []
        partial_lower = partial_query.lower()
        
        # Get suggestions from popular terms
        for term, count in self.search_stats["popular_terms"].most_common(20):
            if term.startswith(partial_lower) and term != partial_lower:
                suggestions.append(term)
        
        # Add some common log-related suggestions
        common_suggestions = [
            "authentication error", "payment timeout", "database connection",
            "api response", "user session", "cache miss", "memory usage",
            "service health", "query performance", "rate limit"
        ]
        
        for suggestion in common_suggestions:
            if suggestion.startswith(partial_lower) and suggestion not in suggestions:
                suggestions.append(suggestion)
        
        return suggestions[:10]
    
    async def get_stats(self) -> Dict:
        """Get search engine statistics"""
        return {
            "total_documents": self.total_documents,
            "total_searches": self.search_stats["total_searches"],
            "avg_response_time_ms": round(self.search_stats["avg_response_time"], 2),
            "popular_terms": dict(self.search_stats["popular_terms"].most_common(10)),
            "index_size": self.document_vectors.shape if self.document_vectors is not None else 0
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        print("Search engine cleanup completed")
