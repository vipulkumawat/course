import re
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import logging

logger = logging.getLogger(__name__)

class LogFeatureExtractor:
    def __init__(self, config):
        self.config = config
        self.vectorizer = TfidfVectorizer(
            max_features=config["max_features"],
            ngram_range=config["ngram_range"],
            min_df=config["min_df"],
            max_df=config["max_df"],
            stop_words='english'
        )
        self.label_encoders = {}
        self.is_fitted = False
        
    def preprocess_text(self, text):
        """Clean and preprocess log text"""
        if not isinstance(text, str):
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove timestamps, IPs, and common log patterns
        text = re.sub(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', '', text)
        text = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '', text)
        text = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '', text)
        
        # Remove special characters except spaces
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
        
    def extract_temporal_features(self, timestamps):
        """Extract time-based features"""
        features = []
        for ts in timestamps:
            try:
                dt = pd.to_datetime(ts)
                features.append([
                    dt.hour,
                    dt.dayofweek,
                    dt.minute // 15,  # 15-minute buckets
                    1 if 9 <= dt.hour <= 17 else 0,  # business hours
                ])
            except:
                features.append([0, 0, 0, 0])
                
        return np.array(features)
        
    def extract_metadata_features(self, metadata_list):
        """Extract features from log metadata"""
        features = []
        for i, meta in enumerate(metadata_list):
            # Handle both dict and string metadata
            if isinstance(meta, dict):
                service_len = len(meta.get('service', ''))
                component_len = len(meta.get('component', ''))
                request_id_len = len(str(meta.get('request_id', '')))
                has_user_id = 1 if meta.get('user_id') else 0
            else:
                # If metadata is a string or other type, use default values
                service_len = 0
                component_len = 0
                request_id_len = 0
                has_user_id = 0
            
            features.append([
                service_len,
                component_len,
                request_id_len,
                has_user_id
            ])
            
        return np.array(features)
        
    def fit_transform(self, logs_df):
        """Fit feature extractors and transform data"""
        logger.info("Fitting feature extractors...")
        
        # Preprocess text
        preprocessed_text = [self.preprocess_text(text) for text in logs_df['message']]
        
        # Fit and transform text features
        text_features = self.vectorizer.fit_transform(preprocessed_text)
        
        # Extract temporal features
        temporal_features = self.extract_temporal_features(logs_df['timestamp'])
        
        # Extract metadata features
        metadata_features = self.extract_metadata_features(logs_df['metadata'])
        
        # Combine all features
        combined_features = np.hstack([
            text_features.toarray(),
            temporal_features,
            metadata_features
        ])
        
        self.is_fitted = True
        logger.info(f"Feature extraction complete. Shape: {combined_features.shape}")
        
        return combined_features
        
    def transform(self, logs_df):
        """Transform new data using fitted extractors"""
        if not self.is_fitted:
            raise ValueError("Feature extractor must be fitted first")
            
        # Preprocess text
        preprocessed_text = [self.preprocess_text(text) for text in logs_df['message']]
        
        # Transform text features
        text_features = self.vectorizer.transform(preprocessed_text)
        
        # Extract other features
        temporal_features = self.extract_temporal_features(logs_df['timestamp'])
        metadata_features = self.extract_metadata_features(logs_df['metadata'])
        
        # Combine features
        combined_features = np.hstack([
            text_features.toarray(),
            temporal_features,
            metadata_features
        ])
        
        return combined_features 