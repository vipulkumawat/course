import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import logging

class LogFeatureExtractor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.text_vectorizer = None
        self.label_encoders = {}
        self.feature_names = []
        self.logger = logging.getLogger(__name__)
        
        self._initialize_extractors()
    
    def _initialize_extractors(self):
        """Initialize feature extraction components"""
        text_config = self.config['clustering']['feature_extraction']['text_features']
        
        self.text_vectorizer = TfidfVectorizer(
            max_features=text_config['max_features'],
            ngram_range=tuple(text_config['ngram_range']),
            stop_words=text_config['stop_words']
        )
    
    def fit_extractors(self, log_entries: List[Dict[str, Any]]) -> None:
        """Fit feature extractors on historical log data"""
        self.logger.info("Fitting feature extractors...")
        
        # Extract text messages for TF-IDF fitting
        messages = [entry.get('message', '') for entry in log_entries]
        self.text_vectorizer.fit(messages)
        
        # Fit label encoders for categorical features
        categorical_fields = ['service', 'level', 'component']
        for field in categorical_fields:
            values = [entry.get(field, 'unknown') for entry in log_entries]
            unique_values = list(set(values))
            
            encoder = LabelEncoder()
            encoder.fit(unique_values)
            self.label_encoders[field] = encoder
        
        # Build feature names list
        self._build_feature_names()
        
        self.logger.info(f"Feature extractors fitted. Total features: {len(self.feature_names)}")
    
    def extract_features(self, log_entry: Dict[str, Any]) -> Tuple[np.ndarray, List[str]]:
        """Extract features from a single log entry"""
        features = []
        
        # 1. Temporal features
        temporal_features = self._extract_temporal_features(log_entry)
        features.extend(temporal_features)
        
        # 2. Structural features
        structural_features = self._extract_structural_features(log_entry)
        features.extend(structural_features)
        
        # 3. Content features (TF-IDF)
        content_features = self._extract_content_features(log_entry)
        features.extend(content_features)
        
        # 4. Network features
        network_features = self._extract_network_features(log_entry)
        features.extend(network_features)
        
        # 5. Behavioral features
        behavioral_features = self._extract_behavioral_features(log_entry)
        features.extend(behavioral_features)
        
        return np.array(features), self.feature_names
    
    def _extract_temporal_features(self, log_entry: Dict[str, Any]) -> List[float]:
        """Extract time-based features"""
        features = []
        
        try:
            timestamp_str = log_entry.get('timestamp', '')
            if timestamp_str:
                # Parse timestamp
                if 'T' in timestamp_str:
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                # Hour of day (cyclical encoding)
                hour = dt.hour
                features.extend([
                    np.sin(2 * np.pi * hour / 24),
                    np.cos(2 * np.pi * hour / 24)
                ])
                
                # Day of week (cyclical encoding)
                day_of_week = dt.weekday()
                features.extend([
                    np.sin(2 * np.pi * day_of_week / 7),
                    np.cos(2 * np.pi * day_of_week / 7)
                ])
                
                # Day of month
                features.append(dt.day / 31.0)
                
                # Month (cyclical encoding)
                month = dt.month
                features.extend([
                    np.sin(2 * np.pi * month / 12),
                    np.cos(2 * np.pi * month / 12)
                ])
                
            else:
                # Default values if no timestamp
                features.extend([0.0] * 7)
                
        except Exception as e:
            self.logger.warning(f"Error extracting temporal features: {e}")
            features.extend([0.0] * 7)
        
        return features
    
    def _extract_structural_features(self, log_entry: Dict[str, Any]) -> List[float]:
        """Extract structural features from log format"""
        features = []
        
        # Service name (encoded)
        service = log_entry.get('service', 'unknown')
        if 'service' in self.label_encoders:
            try:
                service_encoded = self.label_encoders['service'].transform([service])[0]
                features.append(float(service_encoded))
            except ValueError:
                features.append(0.0)  # Unknown service
        else:
            features.append(0.0)
        
        # Log level (encoded)
        level = log_entry.get('level', 'INFO')
        if 'level' in self.label_encoders:
            try:
                level_encoded = self.label_encoders['level'].transform([level])[0]
                features.append(float(level_encoded))
            except ValueError:
                features.append(0.0)  # Unknown level
        else:
            features.append(0.0)
        
        # Component (encoded)
        component = log_entry.get('component', 'unknown')
        if 'component' in self.label_encoders:
            try:
                component_encoded = self.label_encoders['component'].transform([component])[0]
                features.append(float(component_encoded))
            except ValueError:
                features.append(0.0)  # Unknown component
        else:
            features.append(0.0)
        
        # Message length
        message = log_entry.get('message', '')
        features.append(len(message) / 1000.0)  # Normalized
        
        # Number of numeric values in message
        numeric_count = len(re.findall(r'\d+', message))
        features.append(numeric_count / 10.0)  # Normalized
        
        return features
    
    def _extract_content_features(self, log_entry: Dict[str, Any]) -> List[float]:
        """Extract TF-IDF features from log message content"""
        message = log_entry.get('message', '')
        
        if self.text_vectorizer and hasattr(self.text_vectorizer, 'vocabulary_'):
            # Transform message to TF-IDF vector
            tfidf_vector = self.text_vectorizer.transform([message])
            return tfidf_vector.toarray()[0].tolist()
        else:
            # Return zero vector if not fitted
            max_features = self.config['clustering']['feature_extraction']['text_features']['max_features']
            return [0.0] * max_features
    
    def _extract_network_features(self, log_entry: Dict[str, Any]) -> List[float]:
        """Extract network-related features"""
        features = []
        
        # Source IP features
        source_ip = log_entry.get('source_ip', '0.0.0.0')
        ip_parts = source_ip.split('.')
        if len(ip_parts) == 4:
            try:
                # Convert IP to numeric features
                ip_numeric = sum(int(part) * (256 ** (3 - i)) for i, part in enumerate(ip_parts))
                features.append(ip_numeric / (256**4))  # Normalized
                
                # Subnet features
                subnet_16 = '.'.join(ip_parts[:2])
                subnet_24 = '.'.join(ip_parts[:3])
                features.extend([
                    hash(subnet_16) % 1000 / 1000.0,  # Subnet /16 hash
                    hash(subnet_24) % 1000 / 1000.0   # Subnet /24 hash
                ])
            except ValueError:
                features.extend([0.0, 0.0, 0.0])
        else:
            features.extend([0.0, 0.0, 0.0])
        
        # Request size
        request_size = log_entry.get('request_size', 0)
        features.append(min(request_size / 10000.0, 1.0))  # Normalized and capped
        
        # Response size
        response_size = log_entry.get('response_size', 0)
        features.append(min(response_size / 100000.0, 1.0))  # Normalized and capped
        
        return features
    
    def _extract_behavioral_features(self, log_entry: Dict[str, Any]) -> List[float]:
        """Extract behavioral and performance features"""
        features = []
        
        # Response time
        response_time = log_entry.get('response_time', 0)
        features.append(min(response_time / 5000.0, 1.0))  # Normalized to 5s max
        
        # HTTP status code (if present)
        status_code = log_entry.get('status_code', 200)
        features.extend([
            1.0 if 200 <= status_code < 300 else 0.0,  # Success
            1.0 if 400 <= status_code < 500 else 0.0,  # Client error
            1.0 if 500 <= status_code < 600 else 0.0   # Server error
        ])
        
        # Error indicators in message
        message = log_entry.get('message', '').lower()
        error_keywords = ['error', 'exception', 'fail', 'timeout', 'denied']
        features.append(sum(1.0 for keyword in error_keywords if keyword in message) / len(error_keywords))
        
        # Performance indicators
        perf_keywords = ['slow', 'latency', 'bottleneck', 'queue', 'wait']
        features.append(sum(1.0 for keyword in perf_keywords if keyword in message) / len(perf_keywords))
        
        return features
    
    def _build_feature_names(self):
        """Build list of feature names for interpretability"""
        self.feature_names = []
        
        # Temporal features
        self.feature_names.extend([
            'hour_sin', 'hour_cos',
            'day_of_week_sin', 'day_of_week_cos',
            'day_of_month',
            'month_sin', 'month_cos'
        ])
        
        # Structural features
        self.feature_names.extend([
            'service_encoded', 'level_encoded', 'component_encoded',
            'message_length', 'numeric_count'
        ])
        
        # Content features (TF-IDF)
        if self.text_vectorizer and hasattr(self.text_vectorizer, 'get_feature_names_out'):
            tfidf_names = [f'tfidf_{name}' for name in self.text_vectorizer.get_feature_names_out()]
            self.feature_names.extend(tfidf_names)
        else:
            max_features = self.config['clustering']['feature_extraction']['text_features']['max_features']
            self.feature_names.extend([f'tfidf_{i}' for i in range(max_features)])
        
        # Network features
        self.feature_names.extend([
            'ip_numeric', 'subnet_16_hash', 'subnet_24_hash',
            'request_size', 'response_size'
        ])
        
        # Behavioral features
        self.feature_names.extend([
            'response_time', 'status_success', 'status_client_error',
            'status_server_error', 'error_indicators', 'performance_indicators'
        ])
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names"""
        return self.feature_names.copy()
