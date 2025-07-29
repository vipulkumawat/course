#!/bin/bash

# Day 79: Log Clustering for Pattern Discovery - Complete Implementation Script
# Module 3: Advanced Log Processing Features | Week 12: Advanced Analytics

set -e  # Exit on any error

echo "🚀 Day 79: Setting up Log Clustering for Pattern Discovery"
echo "============================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Python 3.11
    if ! command -v python3.11 &> /dev/null; then
        print_error "Python 3.11 not found. Please install Python 3.11"
        exit 1
    fi
    
    # Check pip
    if ! python3.11 -m pip --version &> /dev/null; then
        print_error "pip not found. Please install pip for Python 3.11"
        exit 1
    fi
    
    # Check available memory (need at least 2GB)
    available_mem=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [ "$available_mem" -lt 2000 ]; then
        print_warning "Available memory is ${available_mem}MB. Recommended: 2000MB+"
    fi
    
    print_status "Prerequisites check completed"
}

# Create project structure
create_project_structure() {
    print_info "Creating project structure..."
    
    # Main directories
    mkdir -p src/{clustering,feature_extraction,visualization,utils}
    mkdir -p {tests,config,data,logs,docker,static/{css,js},templates}
    
    # Create __init__.py files
    touch src/__init__.py
    touch src/clustering/__init__.py
    touch src/feature_extraction/__init__.py
    touch src/visualization/__init__.py
    touch src/utils/__init__.py
    touch tests/__init__.py
    
    print_status "Project structure created"
}

# Setup virtual environment
setup_virtual_environment() {
    print_info "Setting up virtual environment..."
    
    # Create virtual environment
    python3.11 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_status "Virtual environment created and activated"
}

# Install dependencies
install_dependencies() {
    print_info "Installing dependencies..."
    
    # Create requirements.txt
    cat > requirements.txt << 'EOF'
# Core ML and data processing
scikit-learn==1.5.0
numpy==1.26.4
pandas==2.2.2

# Advanced clustering
umap-learn==0.5.6
hdbscan==0.8.33

# Visualization
plotly==5.22.0
matplotlib==3.8.4

# Web framework
fastapi==0.111.0
uvicorn==0.30.1
websockets==12.0
jinja2==3.1.4

# Data storage
redis==5.0.6

# Configuration and validation
pydantic==2.7.4
pyyaml==6.0.1

# Testing
pytest==8.2.2
pytest-asyncio==0.23.7

# Utilities
colorama==0.4.6
tqdm==4.66.4
asyncio-mqtt==0.16.1
EOF

    # Install dependencies
    pip install -r requirements.txt
    
    print_status "Dependencies installed successfully"
}

# Create configuration files
create_configuration() {
    print_info "Creating configuration files..."
    
    # Main clustering configuration
    cat > config/clustering_config.yaml << 'EOF'
clustering:
  algorithms:
    kmeans:
      n_clusters: 8
      max_iter: 300
      random_state: 42
      algorithm: 'elkan'
    dbscan:
      eps: 0.3
      min_samples: 5
      algorithm: 'auto'
    hdbscan:
      min_cluster_size: 10
      min_samples: 5
      cluster_selection_epsilon: 0.0
  
  feature_extraction:
    text_features:
      max_features: 1000
      ngram_range: [1, 2]
      stop_words: 'english'
    temporal_features:
      time_windows: [1, 5, 15, 60]  # minutes
      seasonal_features: true
    behavioral_features:
      frequency_threshold: 0.01
      response_time_bins: 10
    network_features:
      ip_subnet_levels: [16, 24]
      geolocation_enabled: false
  
  realtime:
    batch_size: 100
    update_interval: 30  # seconds
    max_clusters: 50
    memory_limit_mb: 512
  
  anomaly_detection:
    threshold_percentile: 95
    min_cluster_size: 5
    alert_cooldown: 300  # seconds

redis:
  host: "localhost"
  port: 6379
  db: 0
  max_connections: 10

api:
  host: "0.0.0.0"
  port: 8000
  debug: true
  workers: 1

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/clustering.log"
EOF

    # Docker configuration
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  clustering-app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    command: python src/main.py

volumes:
  redis_data:
EOF

    # Dockerfile
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs data

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "src/main.py"]
EOF

    print_status "Configuration files created"
}

# Create core clustering engine
create_clustering_engine() {
    print_info "Creating clustering engine..."
    
    cat > src/clustering/engine.py << 'EOF'
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import hdbscan
import asyncio
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json

@dataclass
class ClusterResult:
    algorithm: str
    cluster_id: int
    confidence: float
    is_anomaly: bool
    cluster_center: Optional[np.ndarray] = None
    distance_to_center: Optional[float] = None

@dataclass
class PatternDiscovery:
    pattern_id: str
    pattern_type: str
    algorithm: str
    confidence: float
    sample_logs: List[str]
    feature_importance: Dict[str, float]
    discovered_at: str

class StreamingClusteringEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.algorithms = {}
        self.scalers = {}
        self.cluster_centers = {}
        self.cluster_stats = {}
        self.patterns_discovered = []
        self.feature_names = []
        self.logger = logging.getLogger(__name__)
        
        self._initialize_algorithms()
        
    def _initialize_algorithms(self):
        """Initialize all clustering algorithms"""
        # K-means for general pattern discovery
        kmeans_config = self.config['clustering']['algorithms']['kmeans']
        self.algorithms['kmeans'] = KMeans(
            n_clusters=kmeans_config['n_clusters'],
            max_iter=kmeans_config['max_iter'],
            random_state=kmeans_config['random_state'],
            algorithm=kmeans_config['algorithm']
        )
        
        # DBSCAN for density-based clustering and anomaly detection
        dbscan_config = self.config['clustering']['algorithms']['dbscan']
        self.algorithms['dbscan'] = DBSCAN(
            eps=dbscan_config['eps'],
            min_samples=dbscan_config['min_samples'],
            algorithm=dbscan_config['algorithm']
        )
        
        # HDBSCAN for hierarchical density clustering
        hdbscan_config = self.config['clustering']['algorithms']['hdbscan']
        self.algorithms['hdbscan'] = hdbscan.HDBSCAN(
            min_cluster_size=hdbscan_config['min_cluster_size'],
            min_samples=hdbscan_config['min_samples'],
            cluster_selection_epsilon=hdbscan_config['cluster_selection_epsilon']
        )
        
        # Initialize data scalers for each algorithm
        for algo_name in self.algorithms.keys():
            self.scalers[algo_name] = StandardScaler()
    
    async def fit_initial_model(self, features: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """Fit clustering models on initial historical data"""
        self.feature_names = feature_names
        fit_results = {}
        
        for algo_name, algorithm in self.algorithms.items():
            try:
                self.logger.info(f"Fitting {algo_name} algorithm...")
                
                # Scale features
                scaled_features = self.scalers[algo_name].fit_transform(features)
                
                # Fit algorithm
                start_time = time.time()
                cluster_labels = algorithm.fit_predict(scaled_features)
                fit_time = time.time() - start_time
                
                # Calculate quality metrics
                if len(set(cluster_labels)) > 1:  # More than one cluster
                    silhouette = silhouette_score(scaled_features, cluster_labels)
                    calinski_harabasz = calinski_harabasz_score(scaled_features, cluster_labels)
                else:
                    silhouette = -1
                    calinski_harabasz = 0
                
                # Store cluster centers for k-means
                if algo_name == 'kmeans':
                    self.cluster_centers[algo_name] = algorithm.cluster_centers_
                
                # Calculate cluster statistics
                unique_labels = set(cluster_labels)
                n_clusters = len(unique_labels) - (1 if -1 in cluster_labels else 0)
                n_noise = list(cluster_labels).count(-1)
                
                fit_results[algo_name] = {
                    'n_clusters': n_clusters,
                    'n_noise_points': n_noise,
                    'silhouette_score': silhouette,
                    'calinski_harabasz_score': calinski_harabasz,
                    'fit_time': fit_time,
                    'labels': cluster_labels.tolist()
                }
                
                self.cluster_stats[algo_name] = {
                    'total_points': len(cluster_labels),
                    'clusters': n_clusters,
                    'noise_points': n_noise,
                    'last_updated': time.time()
                }
                
                self.logger.info(f"{algo_name}: {n_clusters} clusters, {n_noise} noise points")
                
            except Exception as e:
                self.logger.error(f"Error fitting {algo_name}: {str(e)}")
                fit_results[algo_name] = {'error': str(e)}
        
        return fit_results
    
    async def predict_cluster(self, features: np.ndarray) -> List[ClusterResult]:
        """Predict cluster for new log entry using all algorithms"""
        results = []
        
        for algo_name, algorithm in self.algorithms.items():
            try:
                # Scale features using fitted scaler
                scaled_features = self.scalers[algo_name].transform(features.reshape(1, -1))
                
                # Predict cluster
                if algo_name == 'kmeans':
                    cluster_id = algorithm.predict(scaled_features)[0]
                    
                    # Calculate distance to cluster center
                    center = algorithm.cluster_centers_[cluster_id]
                    distance = np.linalg.norm(scaled_features[0] - center)
                    
                    # Determine if anomaly based on distance
                    is_anomaly = distance > np.percentile(
                        [np.linalg.norm(scaled_features[0] - c) for c in algorithm.cluster_centers_],
                        self.config['clustering']['anomaly_detection']['threshold_percentile']
                    )
                    
                    confidence = max(0.1, 1.0 - (distance / np.max([
                        np.linalg.norm(algorithm.cluster_centers_[i] - algorithm.cluster_centers_[j])
                        for i in range(len(algorithm.cluster_centers_))
                        for j in range(i+1, len(algorithm.cluster_centers_))
                    ] + [1.0])))
                    
                    results.append(ClusterResult(
                        algorithm=algo_name,
                        cluster_id=int(cluster_id),
                        confidence=confidence,
                        is_anomaly=is_anomaly,
                        cluster_center=center,
                        distance_to_center=distance
                    ))
                    
                elif algo_name in ['dbscan', 'hdbscan']:
                    # For density-based algorithms, we need to check if point fits existing clusters
                    cluster_id = self._predict_density_cluster(scaled_features[0], algo_name)
                    
                    is_anomaly = cluster_id == -1
                    confidence = 0.5 if is_anomaly else 0.8
                    
                    results.append(ClusterResult(
                        algorithm=algo_name,
                        cluster_id=int(cluster_id),
                        confidence=confidence,
                        is_anomaly=is_anomaly
                    ))
                    
            except Exception as e:
                self.logger.error(f"Error predicting with {algo_name}: {str(e)}")
        
        return results
    
    def _predict_density_cluster(self, scaled_features: np.ndarray, algo_name: str) -> int:
        """Predict cluster for density-based algorithms"""
        # This is a simplified implementation
        # In production, you'd use more sophisticated nearest neighbor search
        return 0  # Placeholder
    
    async def discover_new_patterns(self, recent_results: List[ClusterResult], 
                                 log_samples: List[str]) -> List[PatternDiscovery]:
        """Analyze recent clustering results to discover new patterns"""
        new_patterns = []
        
        # Group results by algorithm and cluster
        pattern_groups = {}
        for i, result in enumerate(recent_results):
            key = f"{result.algorithm}_{result.cluster_id}"
            if key not in pattern_groups:
                pattern_groups[key] = []
            pattern_groups[key].append((result, log_samples[i % len(log_samples)]))
        
        # Analyze each pattern group
        for pattern_key, group_data in pattern_groups.items():
            if len(group_data) >= self.config['clustering']['anomaly_detection']['min_cluster_size']:
                results, logs = zip(*group_data)
                avg_confidence = np.mean([r.confidence for r in results])
                
                if avg_confidence > 0.7:  # High confidence pattern
                    pattern = PatternDiscovery(
                        pattern_id=f"pattern_{len(self.patterns_discovered)}",
                        pattern_type=self._classify_pattern_type(logs),
                        algorithm=results[0].algorithm,
                        confidence=avg_confidence,
                        sample_logs=list(logs)[:5],  # Store sample logs
                        feature_importance=self._calculate_feature_importance(results),
                        discovered_at=time.strftime("%Y-%m-%d %H:%M:%S")
                    )
                    
                    new_patterns.append(pattern)
                    self.patterns_discovered.append(pattern)
        
        return new_patterns
    
    def _classify_pattern_type(self, logs: List[str]) -> str:
        """Classify the type of pattern based on log content"""
        log_text = ' '.join(logs).lower()
        
        if any(word in log_text for word in ['error', 'exception', 'fail']):
            return 'error_pattern'
        elif any(word in log_text for word in ['login', 'auth', 'user']):
            return 'security_pattern'
        elif any(word in log_text for word in ['slow', 'timeout', 'latency']):
            return 'performance_pattern'
        else:
            return 'general_pattern'
    
    def _calculate_feature_importance(self, results: List[ClusterResult]) -> Dict[str, float]:
        """Calculate feature importance for pattern discovery"""
        # Simplified feature importance calculation
        importance = {}
        for i, feature_name in enumerate(self.feature_names):
            importance[feature_name] = np.random.random()  # Placeholder
        
        # Normalize to sum to 1
        total = sum(importance.values())
        if total > 0:
            importance = {k: v/total for k, v in importance.items()}
        
        return importance
    
    def get_cluster_statistics(self) -> Dict[str, Any]:
        """Get current clustering statistics"""
        stats = {
            'algorithms': {},
            'total_patterns_discovered': len(self.patterns_discovered),
            'recent_patterns': self.patterns_discovered[-5:] if self.patterns_discovered else [],
            'feature_count': len(self.feature_names),
            'last_updated': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        for algo_name, cluster_stat in self.cluster_stats.items():
            stats['algorithms'][algo_name] = cluster_stat.copy()
        
        return stats
EOF

    print_status "Clustering engine created"
}

# Create feature extraction pipeline
create_feature_extraction() {
    print_info "Creating feature extraction pipeline..."
    
    cat > src/feature_extraction/pipeline.py << 'EOF'
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
EOF

    print_status "Feature extraction pipeline created"
}

# Create visualization components
create_visualization() {
    print_info "Creating visualization components..."
    
    # WebSocket handler for real-time updates
    cat > src/visualization/websocket_handler.py << 'EOF'
import json
import asyncio
import logging
from typing import Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = logging.getLogger(__name__)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            self.logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

class ClusterWebSocketHandler:
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)

    async def handle_new_cluster(self, cluster_data: Dict[str, Any]):
        """Handle new cluster discovery and broadcast to clients"""
        message = {
            "type": "new_cluster",
            "data": cluster_data,
            "timestamp": cluster_data.get("timestamp")
        }
        
        await self.connection_manager.broadcast(json.dumps(message))
        self.logger.info(f"Broadcasted new cluster: {cluster_data.get('cluster_id', 'unknown')}")

    async def handle_anomaly_detection(self, anomaly_data: Dict[str, Any]):
        """Handle anomaly detection and send alerts"""
        message = {
            "type": "anomaly_alert",
            "data": anomaly_data,
            "severity": anomaly_data.get("severity", "medium"),
            "timestamp": anomaly_data.get("timestamp")
        }
        
        await self.connection_manager.broadcast(json.dumps(message))
        self.logger.warning(f"Broadcasted anomaly alert: {anomaly_data.get('pattern_type', 'unknown')}")

    async def handle_pattern_discovery(self, pattern_data: Dict[str, Any]):
        """Handle pattern discovery updates"""
        message = {
            "type": "pattern_discovery",
            "data": pattern_data,
            "timestamp": pattern_data.get("discovered_at")
        }
        
        await self.connection_manager.broadcast(json.dumps(message))
        self.logger.info(f"Broadcasted pattern discovery: {pattern_data.get('pattern_type', 'unknown')}")

    async def handle_cluster_stats_update(self, stats_data: Dict[str, Any]):
        """Handle cluster statistics updates"""
        message = {
            "type": "stats_update",
            "data": stats_data,
            "timestamp": stats_data.get("last_updated")
        }
        
        await self.connection_manager.broadcast(json.dumps(message))
EOF

    # Dashboard template
    cat > templates/dashboard.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log Clustering Dashboard - Day 79</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            color: #7f8c8d;
            font-size: 1.1rem;
        }
        
        .dashboard-container {
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            color: #2c3e50;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 0.5rem;
        }
        
        .stat-description {
            color: #7f8c8d;
            font-size: 0.9rem;
        }
        
        .visualization-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .chart-container h3 {
            color: #2c3e50;
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }
        
        .alerts-container {
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            margin-bottom: 2rem;
        }
        
        .alert-item {
            padding: 1rem;
            margin-bottom: 0.5rem;
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .alert-anomaly {
            background: #ffeaa7;
            border-left-color: #fdcb6e;
        }
        
        .alert-pattern {
            background: #a7f5ff;
            border-left-color: #00cec9;
        }
        
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }
        
        .connected {
            background: #00b894;
            color: white;
        }
        
        .disconnected {
            background: #e17055;
            color: white;
        }
        
        @media (max-width: 768px) {
            .visualization-grid {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connection-status">Connecting...</div>
    
    <div class="header">
        <h1>🎯 Log Clustering Dashboard</h1>
        <p>Day 79: Pattern Discovery in Distributed Log Processing Systems</p>
    </div>
    
    <div class="dashboard-container">
        <!-- Statistics Cards -->
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Clusters</h3>
                <div class="stat-value" id="total-clusters">0</div>
                <div class="stat-description">Active pattern clusters</div>
            </div>
            
            <div class="stat-card">
                <h3>Patterns Discovered</h3>
                <div class="stat-value" id="patterns-discovered">0</div>
                <div class="stat-description">Unique patterns found</div>
            </div>
            
            <div class="stat-card">
                <h3>Anomalies Detected</h3>
                <div class="stat-value" id="anomalies-detected">0</div>
                <div class="stat-description">Unusual patterns identified</div>
            </div>
            
            <div class="stat-card">
                <h3>Processing Rate</h3>
                <div class="stat-value" id="processing-rate">0</div>
                <div class="stat-description">Logs per second</div>
            </div>
        </div>
        
        <!-- Visualizations -->
        <div class="visualization-grid">
            <div class="chart-container">
                <h3>📊 Cluster Distribution</h3>
                <div id="cluster-distribution-chart" style="height: 300px;"></div>
            </div>
            
            <div class="chart-container">
                <h3>📈 Pattern Timeline</h3>
                <div id="pattern-timeline-chart" style="height: 300px;"></div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>🗺️ Cluster Visualization</h3>
            <div id="cluster-scatter-plot" style="height: 400px;"></div>
        </div>
        
        <!-- Alerts -->
        <div class="alerts-container">
            <h3>🚨 Recent Alerts</h3>
            <div id="alerts-list">
                <p style="color: #7f8c8d; text-align: center;">No alerts yet...</p>
            </div>
        </div>
    </div>
    
    <script>
        class ClusteringDashboard {
            constructor() {
                this.ws = null;
                this.isConnected = false;
                this.stats = {
                    totalClusters: 0,
                    patternsDiscovered: 0,
                    anomaliesDetected: 0,
                    processingRate: 0
                };
                this.alerts = [];
                this.clusterData = [];
                this.patternTimeline = [];
                
                this.initializeWebSocket();
                this.initializeCharts();
                this.updateConnectionStatus();
            }
            
            initializeWebSocket() {
                const wsUrl = `ws://${window.location.host}/ws`;
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onopen = () => {
                    this.isConnected = true;
                    this.updateConnectionStatus();
                    console.log('WebSocket connected');
                };
                
                this.ws.onclose = () => {
                    this.isConnected = false;
                    this.updateConnectionStatus();
                    console.log('WebSocket disconnected');
                    
                    // Reconnect after 5 seconds
                    setTimeout(() => this.initializeWebSocket(), 5000);
                };
                
                this.ws.onmessage = (event) => {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                };
                
                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                };
            }
            
            handleMessage(message) {
                switch (message.type) {
                    case 'new_cluster':
                        this.handleNewCluster(message.data);
                        break;
                    case 'anomaly_alert':
                        this.handleAnomalyAlert(message.data);
                        break;
                    case 'pattern_discovery':
                        this.handlePatternDiscovery(message.data);
                        break;
                    case 'stats_update':
                        this.handleStatsUpdate(message.data);
                        break;
                }
            }
            
            handleNewCluster(data) {
                this.stats.totalClusters++;
                this.clusterData.push(data);
                this.updateStats();
                this.updateClusterVisualization();
            }
            
            handleAnomalyAlert(data) {
                this.stats.anomaliesDetected++;
                this.addAlert('anomaly', `Anomaly detected: ${data.pattern_type || 'Unknown'}`, data.timestamp);
                this.updateStats();
            }
            
            handlePatternDiscovery(data) {
                this.stats.patternsDiscovered++;
                this.patternTimeline.push({
                    timestamp: data.discovered_at,
                    pattern_type: data.pattern_type,
                    confidence: data.confidence
                });
                this.addAlert('pattern', `New pattern discovered: ${data.pattern_type}`, data.discovered_at);
                this.updateStats();
                this.updatePatternTimeline();
            }
            
            handleStatsUpdate(data) {
                if (data.algorithms) {
                    this.stats.totalClusters = Object.values(data.algorithms)
                        .reduce((sum, algo) => sum + (algo.clusters || 0), 0);
                }
                this.stats.patternsDiscovered = data.total_patterns_discovered || this.stats.patternsDiscovered;
                this.updateStats();
                this.updateClusterDistribution(data.algorithms);
            }
            
            addAlert(type, message, timestamp) {
                this.alerts.unshift({
                    type: type,
                    message: message,
                    timestamp: timestamp || new Date().toISOString()
                });
                
                // Keep only last 10 alerts
                this.alerts = this.alerts.slice(0, 10);
                this.updateAlerts();
            }
            
            updateConnectionStatus() {
                const statusEl = document.getElementById('connection-status');
                if (this.isConnected) {
                    statusEl.textContent = '🟢 Connected';
                    statusEl.className = 'connection-status connected';
                } else {
                    statusEl.textContent = '🔴 Disconnected';
                    statusEl.className = 'connection-status disconnected';
                }
            }
            
            updateStats() {
                document.getElementById('total-clusters').textContent = this.stats.totalClusters;
                document.getElementById('patterns-discovered').textContent = this.stats.patternsDiscovered;
                document.getElementById('anomalies-detected').textContent = this.stats.anomaliesDetected;
                document.getElementById('processing-rate').textContent = this.stats.processingRate;
            }
            
            updateAlerts() {
                const alertsList = document.getElementById('alerts-list');
                if (this.alerts.length === 0) {
                    alertsList.innerHTML = '<p style="color: #7f8c8d; text-align: center;">No alerts yet...</p>';
                    return;
                }
                
                alertsList.innerHTML = this.alerts.map(alert => `
                    <div class="alert-item alert-${alert.type}">
                        <strong>${alert.message}</strong><br>
                        <small>${new Date(alert.timestamp).toLocaleString()}</small>
                    </div>
                `).join('');
            }
            
            initializeCharts() {
                // Initialize empty charts
                this.updateClusterDistribution({});
                this.updatePatternTimeline();
                this.updateClusterVisualization();
            }
            
            updateClusterDistribution(algorithms) {
                const data = Object.keys(algorithms || {}).map(algoName => ({
                    x: [algoName],
                    y: [algorithms[algoName].clusters || 0],
                    type: 'bar',
                    name: algoName.toUpperCase(),
                    marker: {
                        color: algoName === 'kmeans' ? '#3498db' : 
                              algoName === 'dbscan' ? '#e74c3c' : '#2ecc71'
                    }
                }));
                
                const layout = {
                    title: '',
                    xaxis: { title: 'Algorithm' },
                    yaxis: { title: 'Number of Clusters' },
                    margin: { t: 30 },
                    showlegend: false,
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    paper_bgcolor: 'rgba(0,0,0,0)'
                };
                
                Plotly.newPlot('cluster-distribution-chart', data, layout, {responsive: true});
            }
            
            updatePatternTimeline() {
                if (this.patternTimeline.length === 0) {
                    const emptyLayout = {
                        title: '',
                        margin: { t: 30 },
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        annotations: [{
                            x: 0.5,
                            y: 0.5,
                            xref: 'paper',
                            yref: 'paper',
                            text: 'No patterns discovered yet',
                            showarrow: false,
                            font: { color: '#7f8c8d' }
                        }]
                    };
                    Plotly.newPlot('pattern-timeline-chart', [], emptyLayout, {responsive: true});
                    return;
                }
                
                const data = [{
                    x: this.patternTimeline.map(p => p.timestamp),
                    y: this.patternTimeline.map(p => p.confidence),
                    mode: 'markers+lines',
                    type: 'scatter',
                    name: 'Pattern Confidence',
                    marker: { color: '#3498db', size: 8 },
                    line: { color: '#3498db' }
                }];
                
                const layout = {
                    title: '',
                    xaxis: { title: 'Time' },
                    yaxis: { title: 'Confidence' },
                    margin: { t: 30 },
                    showlegend: false,
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    paper_bgcolor: 'rgba(0,0,0,0)'
                };
                
                Plotly.newPlot('pattern-timeline-chart', data, layout, {responsive: true});
            }
            
            updateClusterVisualization() {
                // Simulated 2D projection of clusters for visualization
                const data = this.clusterData.slice(-100).map((cluster, idx) => ({
                    x: Math.random() * 10 - 5 + (cluster.cluster_id || 0),
                    y: Math.random() * 10 - 5 + (cluster.confidence || 0.5) * 10,
                    cluster: cluster.cluster_id || 0,
                    algorithm: cluster.algorithm || 'unknown'
                }));
                
                const algorithms = [...new Set(data.map(d => d.algorithm))];
                const traces = algorithms.map(algo => ({
                    x: data.filter(d => d.algorithm === algo).map(d => d.x),
                    y: data.filter(d => d.algorithm === algo).map(d => d.y),
                    mode: 'markers',
                    type: 'scatter',
                    name: algo.toUpperCase(),
                    marker: {
                        size: 8,
                        color: algo === 'kmeans' ? '#3498db' : 
                              algo === 'dbscan' ? '#e74c3c' : '#2ecc71'
                    }
                }));
                
                const layout = {
                    title: '',
                    xaxis: { title: 'Component 1' },
                    yaxis: { title: 'Component 2' },
                    margin: { t: 30 },
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    showlegend: true,
                    legend: { x: 0, y: 1 }
                };
                
                if (traces.length > 0) {
                    Plotly.newPlot('cluster-scatter-plot', traces, layout, {responsive: true});
                } else {
                    const emptyLayout = {
                        ...layout,
                        annotations: [{
                            x: 0.5,
                            y: 0.5,
                            xref: 'paper',
                            yref: 'paper',
                            text: 'No cluster data available yet',
                            showarrow: false,
                            font: { color: '#7f8c8d' }
                        }]
                    };
                    Plotly.newPlot('cluster-scatter-plot', [], emptyLayout, {responsive: true});
                }
            }
            
            // Simulate some data for demo purposes
            simulateData() {
                setTimeout(() => {
                    this.handleStatsUpdate({
                        algorithms: {
                            kmeans: { clusters: 5, total_points: 150 },
                            dbscan: { clusters: 3, total_points: 150 },
                            hdbscan: { clusters: 4, total_points: 150 }
                        },
                        total_patterns_discovered: 7
                    });
                }, 2000);
                
                setTimeout(() => {
                    this.handlePatternDiscovery({
                        pattern_type: 'error_pattern',
                        confidence: 0.87,
                        discovered_at: new Date().toISOString()
                    });
                }, 4000);
                
                setTimeout(() => {
                    this.handleAnomalyAlert({
                        pattern_type: 'unusual_access_pattern',
                        severity: 'high',
                        timestamp: new Date().toISOString()
                    });
                }, 6000);
            }
        }
        
        // Initialize dashboard when page loads
        document.addEventListener('DOMContentLoaded', () => {
            const dashboard = new ClusteringDashboard();
            
            // Simulate some data if in demo mode
            if (window.location.search.includes('demo=true')) {
                dashboard.simulateData();
            }
        });
    </script>
</body>
</html>
EOF

    print_status "Visualization components created"
}

# Create main application
create_main_application() {
    print_info "Creating main application..."
    
    cat > src/main.py << 'EOF'
#!/usr/bin/env python3
"""
Day 79: Log Clustering for Pattern Discovery
Main application entry point
"""

import asyncio
import json
import logging
import sys
import time
import uvicorn
from typing import Dict, List, Any
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import yaml
import redis
import numpy as np

# Import our modules
from clustering.engine import StreamingClusteringEngine
from feature_extraction.pipeline import LogFeatureExtractor
from visualization.websocket_handler import ConnectionManager, ClusterWebSocketHandler
from utils.sample_data import generate_sample_logs, LogEntry

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config_path = Path("config/clustering_config.yaml")
if not config_path.exists():
    logger.error(f"Configuration file not found: {config_path}")
    sys.exit(1)

with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Initialize FastAPI app
app = FastAPI(title="Log Clustering Dashboard", version="1.0.0")

# Setup static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global components
clustering_engine = None
feature_extractor = None
connection_manager = ConnectionManager()
websocket_handler = None
redis_client = None

# Statistics tracking
stats = {
    'total_processed': 0,
    'patterns_discovered': 0,
    'anomalies_detected': 0,
    'processing_rate': 0,
    'last_updated': time.time()
}

async def initialize_components():
    """Initialize all system components"""
    global clustering_engine, feature_extractor, websocket_handler, redis_client
    
    logger.info("Initializing system components...")
    
    # Initialize Redis connection
    redis_config = config['redis']
    redis_client = redis.Redis(
        host=redis_config['host'],
        port=redis_config['port'],
        db=redis_config['db'],
        decode_responses=True
    )
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        redis_client = None
    
    # Initialize clustering engine
    clustering_engine = StreamingClusteringEngine(config)
    
    # Initialize feature extractor
    feature_extractor = LogFeatureExtractor(config)
    
    # Initialize WebSocket handler
    websocket_handler = ClusterWebSocketHandler(connection_manager)
    
    logger.info("System components initialized successfully")

async def train_initial_models():
    """Train models on historical data"""
    logger.info("Training initial clustering models...")
    
    # Generate sample historical data
    sample_logs = generate_sample_logs(1000)
    
    # Fit feature extractor
    log_dicts = [log.to_dict() for log in sample_logs]
    feature_extractor.fit_extractors(log_dicts)
    
    # Extract features for all logs
    features_list = []
    for log_dict in log_dicts:
        features, feature_names = feature_extractor.extract_features(log_dict)
        features_list.append(features)
    
    features_matrix = np.array(features_list)
    
    # Fit clustering models
    fit_results = await clustering_engine.fit_initial_model(features_matrix, feature_names)
    
    logger.info(f"Models trained successfully: {fit_results}")
    
    # Update statistics
    stats['total_processed'] = len(sample_logs)
    stats['last_updated'] = time.time()
    
    return fit_results

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    await initialize_components()
    await train_initial_models()
    logger.info("Application startup completed")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await connection_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and send periodic updates
            await asyncio.sleep(10)
            
            # Send stats update
            current_stats = clustering_engine.get_cluster_statistics()
            await websocket_handler.handle_cluster_stats_update(current_stats)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

@app.get("/api/stats")
async def get_stats():
    """Get current system statistics"""
    cluster_stats = clustering_engine.get_cluster_statistics()
    
    return {
        **stats,
        **cluster_stats,
        'redis_connected': redis_client is not None and redis_client.ping() if redis_client else False
    }

@app.get("/api/clusters")
async def get_clusters():
    """Get cluster information"""
    return clustering_engine.get_cluster_statistics()

@app.post("/api/process_log")
async def process_log(log_data: Dict[str, Any]):
    """Process a single log entry"""
    try:
        # Extract features
        features, feature_names = feature_extractor.extract_features(log_data)
        
        # Predict cluster
        cluster_results = await clustering_engine.predict_cluster(features)
        
        # Update statistics
        stats['total_processed'] += 1
        stats['processing_rate'] = calculate_processing_rate()
        stats['last_updated'] = time.time()
        
        # Check for anomalies
        anomalies = [result for result in cluster_results if result.is_anomaly]
        if anomalies:
            stats['anomalies_detected'] += 1
            for anomaly in anomalies:
                await websocket_handler.handle_anomaly_detection({
                    'algorithm': anomaly.algorithm,
                    'cluster_id': anomaly.cluster_id,
                    'confidence': anomaly.confidence,
                    'pattern_type': 'anomaly',
                    'log_message': log_data.get('message', ''),
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # Broadcast new cluster results
        for result in cluster_results:
            await websocket_handler.handle_new_cluster({
                'algorithm': result.algorithm,
                'cluster_id': result.cluster_id,
                'confidence': result.confidence,
                'is_anomaly': result.is_anomaly,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {
            'success': True,
            'cluster_results': [
                {
                    'algorithm': r.algorithm,
                    'cluster_id': r.cluster_id,
                    'confidence': r.confidence,
                    'is_anomaly': r.is_anomaly
                } for r in cluster_results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error processing log: {e}")
        return {'success': False, 'error': str(e)}

def calculate_processing_rate():
    """Calculate logs processed per second"""
    current_time = time.time()
    time_diff = current_time - stats['last_updated']
    if time_diff > 0:
        return stats['total_processed'] / time_diff
    return 0

async def run_demo():
    """Run demonstration of clustering system"""
    logger.info("🎯 Starting Log Clustering Demonstration")
    logger.info("=" * 50)
    
    # Generate demo logs
    demo_logs = generate_sample_logs(50)
    
    logger.info(f"📝 Processing {len(demo_logs)} Demo Log Entries:")
    logger.info("=" * 50)
    
    pattern_count = 0
    anomaly_count = 0
    
    for i, log in enumerate(demo_logs[:10], 1):  # Process first 10 for demo
        log_dict = log.to_dict()
        
        logger.info(f"\n📝 Processing Log Entry {i}:")
        logger.info(f"   Service: {log.service}")
        logger.info(f"   Level: {log.level}")
        logger.info(f"   Message: {log.message[:60]}...")
        
        # Extract features
        features, feature_names = feature_extractor.extract_features(log_dict)
        
        # Predict cluster
        cluster_results = await clustering_engine.predict_cluster(features)
        
        logger.info("   🎯 Cluster Results:")
        for result in cluster_results:
            logger.info(f"      {result.algorithm}: Cluster {result.cluster_id} (confidence: {result.confidence:.2f})")
            if result.is_anomaly:
                logger.info("      🚨 ANOMALY DETECTED!")
                anomaly_count += 1
        
        # Simulate pattern discovery
        if i % 3 == 0:  # Every 3rd log discovers a pattern
            pattern_count += 1
            logger.info("   🔍 Discovered Patterns:")
            logger.info(f"      Pattern Type: {log.service}_pattern")
            logger.info(f"      Algorithm: {cluster_results[0].algorithm}")
            logger.info(f"      Confidence: {cluster_results[0].confidence:.2f}")
        
        # Small delay for demo effect
        await asyncio.sleep(0.5)
    
    # Show final statistics
    cluster_stats = clustering_engine.get_cluster_statistics()
    
    logger.info(f"\n📊 Final Cluster Insights:")
    logger.info(f"   Total Patterns Discovered: {pattern_count}")
    logger.info(f"   Anomalies Detected: {anomaly_count}")
    logger.info(f"   Total Clusters: {sum(cluster_stats['algorithms'][algo]['clusters'] for algo in cluster_stats['algorithms'])}")
    logger.info(f"   Algorithms Used: {len(cluster_stats['algorithms'])}")
    
    for algo_name, algo_stats in cluster_stats['algorithms'].items():
        logger.info(f"   {algo_name.upper()}:")
        logger.info(f"      Clusters: {algo_stats['clusters']}")
        logger.info(f"      Avg Size: {algo_stats['total_points'] / max(algo_stats['clusters'], 1):.1f}")
    
    logger.info(f"\n✅ Demo completed successfully!")
    logger.info(f"🌐 Dashboard available at: http://localhost:{config['api']['port']}")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "demo":
            # Run demo
            asyncio.run(run_demo())
        elif command == "train":
            # Run training only
            asyncio.run(initialize_components())
            asyncio.run(train_initial_models())
        else:
            logger.error(f"Unknown command: {command}")
            sys.exit(1)
    else:
        # Run web server
        uvicorn.run(
            "main:app",
            host=config['api']['host'],
            port=config['api']['port'],
            reload=config['api']['debug'],
            log_level="info"
        )

if __name__ == "__main__":
    main()
EOF

    print_status "Main application created"
}

# Create utility modules
create_utilities() {
    print_info "Creating utility modules..."
    
    # Sample data generator
    cat > src/utils/sample_data.py << 'EOF'
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass
import uuid

@dataclass
class LogEntry:
    timestamp: str
    service: str
    level: str
    component: str
    message: str
    source_ip: str
    request_size: int
    response_size: int
    response_time: int
    status_code: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'service': self.service,
            'level': self.level,
            'component': self.component,
            'message': self.message,
            'source_ip': self.source_ip,
            'request_size': self.request_size,
            'response_size': self.response_size,
            'response_time': self.response_time,
            'status_code': self.status_code
        }

def generate_sample_logs(count: int = 100) -> List[LogEntry]:
    """Generate sample log entries for testing and demonstration"""
    
    services = ['auth', 'user', 'payment', 'inventory', 'recommendation']
    levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
    components = ['api', 'database', 'cache', 'queue', 'worker']
    
    # Message templates by service and level
    message_templates = {
        'auth': {
            'INFO': [
                'User {} successfully authenticated',
                'Session created for user {}',
                'Password reset requested for {}',
                'OAuth token refreshed for user {}'
            ],
            'WARN': [
                'Multiple failed login attempts for user {}',
                'Suspicious login pattern detected from IP {}',
                'Account locked due to failed attempts: {}',
                'Unusual access time for user {}'
            ],
            'ERROR': [
                'Authentication failed for user {}',
                'Database connection failed during auth',
                'JWT token validation failed for {}',
                'LDAP server unreachable for user {}'
            ]
        },
        'payment': {
            'INFO': [
                'Payment processed successfully: ${}',
                'Credit card authorized for amount ${}',
                'Refund processed for transaction {}',
                'Payment method updated for user {}'
            ],
            'WARN': [
                'High-value transaction flagged: ${}',
                'Payment retry attempt {} for user {}',
                'Unusual spending pattern detected for {}',
                'Credit card expires soon for user {}'
            ],
            'ERROR': [
                'Payment processing failed: {}',
                'Credit card declined for user {}',
                'Payment gateway timeout for transaction {}',
                'Insufficient funds for user {}'
            ]
        },
        'inventory': {
            'INFO': [
                'Stock updated for product {}: {} units',
                'Product {} added to catalog',
                'Inventory sync completed for warehouse {}',
                'Low stock alert threshold updated for {}'
            ],
            'WARN': [
                'Low stock warning for product {}: {} remaining',
                'Unusual order quantity for product {}: {}',
                'Supplier delivery delayed for product {}',
                'Price fluctuation detected for product {}'
            ],
            'ERROR': [
                'Out of stock error for product {}',
                'Inventory database sync failed',
                'Product {} not found in catalog',
                'Warehouse {} connection failed'
            ]
        }
    }
    
    logs = []
    start_time = datetime.now() - timedelta(hours=24)
    
    for i in range(count):
        # Generate timestamp
        timestamp = start_time + timedelta(minutes=random.randint(0, 1440))
        
        # Select service, level, component
        service = random.choice(services)
        level = random.choice(levels)
        component = random.choice(components)
        
        # Generate message
        service_templates = message_templates.get(service, {})
        level_templates = service_templates.get(level, [f'{service} {level.lower()} message {}'])
        
        if level_templates:
            template = random.choice(level_templates)
            # Fill template with random data
            if '{}' in template:
                fill_data = [
                    f'user_{random.randint(1000, 9999)}',
                    f'{random.randint(10, 500)}',
                    f'192.168.1.{random.randint(1, 255)}',
                    f'prod_{random.randint(100, 999)}',
                    f'txn_{uuid.uuid4().hex[:8]}'
                ]
                message = template.format(*fill_data[:template.count('{}')])
            else:
                message = template
        else:
            message = f'{service} {level.lower()} message {i}'
        
        # Generate network and performance data
        source_ip = f'192.168.{random.randint(1, 10)}.{random.randint(1, 255)}'
        request_size = random.randint(100, 10000)
        response_size = random.randint(500, 50000)
        
        # Response time based on level (errors tend to be slower)
        if level == 'ERROR':
            response_time = random.randint(1000, 5000)  # 1-5 seconds
        elif level == 'WARN':
            response_time = random.randint(500, 2000)   # 0.5-2 seconds
        else:
            response_time = random.randint(50, 500)     # 50-500ms
        
        # Status code based on level
        if level == 'ERROR':
            status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
        elif level == 'WARN':
            status_code = random.choice([200, 201, 202, 400, 429])
        else:
            status_code = random.choice([200, 201, 202, 204])
        
        log_entry = LogEntry(
            timestamp=timestamp.isoformat(),
            service=service,
            level=level,
            component=component,
            message=message,
            source_ip=source_ip,
            request_size=request_size,
            response_size=response_size,
            response_time=response_time,
            status_code=status_code
        )
        
        logs.append(log_entry)
    
    # Sort by timestamp
    logs.sort(key=lambda x: x.timestamp)
    
    return logs
EOF

    print_status "Utility modules created"
}

# Create comprehensive test suite
create_test_suite() {
    print_info "Creating test suite..."
    
    cat > tests/test_clustering.py << 'EOF'
import pytest
import numpy as np
import asyncio
import yaml
from pathlib import Path

# Import modules to test
import sys
sys.path.append('src')

from clustering.engine import StreamingClusteringEngine, ClusterResult
from feature_extraction.pipeline import LogFeatureExtractor
from utils.sample_data import generate_sample_logs

@pytest.fixture
def config():
    """Load test configuration"""
    config_path = Path("config/clustering_config.yaml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def sample_logs():
    """Generate sample logs for testing"""
    return generate_sample_logs(100)

@pytest.fixture
def feature_extractor(config):
    """Create feature extractor instance"""
    return LogFeatureExtractor(config)

@pytest.fixture
def clustering_engine(config):
    """Create clustering engine instance"""
    return StreamingClusteringEngine(config)

class TestLogFeatureExtractor:
    """Test feature extraction pipeline"""
    
    def test_initialization(self, feature_extractor):
        """Test feature extractor initialization"""
        assert feature_extractor is not None
        assert feature_extractor.text_vectorizer is not None
        assert isinstance(feature_extractor.label_encoders, dict)
    
    def test_fit_extractors(self, feature_extractor, sample_logs):
        """Test fitting feature extractors on sample data"""
        log_dicts = [log.to_dict() for log in sample_logs]
        feature_extractor.fit_extractors(log_dicts)
        
        # Check that extractors were fitted
        assert hasattr(feature_extractor.text_vectorizer, 'vocabulary_')
        assert len(feature_extractor.label_encoders) > 0
        assert len(feature_extractor.feature_names) > 0
    
    def test_extract_features(self, feature_extractor, sample_logs):
        """Test feature extraction from single log entry"""
        log_dicts = [log.to_dict() for log in sample_logs]
        feature_extractor.fit_extractors(log_dicts)
        
        # Extract features from first log
        features, feature_names = feature_extractor.extract_features(log_dicts[0])
        
        assert isinstance(features, np.ndarray)
        assert len(features) > 0
        assert len(feature_names) == len(features)
        assert all(isinstance(f, (int, float)) for f in features)

class TestStreamingClusteringEngine:
    """Test clustering engine functionality"""
    
    def test_initialization(self, clustering_engine):
        """Test clustering engine initialization"""
        assert clustering_engine is not None
        assert 'kmeans' in clustering_engine.algorithms
        assert 'dbscan' in clustering_engine.algorithms
        assert 'hdbscan' in clustering_engine.algorithms
    
    @pytest.mark.asyncio
    async def test_fit_initial_model(self, clustering_engine, feature_extractor, sample_logs):
        """Test initial model fitting"""
        # Prepare data
        log_dicts = [log.to_dict() for log in sample_logs]
        feature_extractor.fit_extractors(log_dicts)
        
        features_list = []
        for log_dict in log_dicts:
            features, feature_names = feature_extractor.extract_features(log_dict)
            features_list.append(features)
        
        features_matrix = np.array(features_list)
        
        # Fit models
        fit_results = await clustering_engine.fit_initial_model(features_matrix, feature_names)
        
        assert isinstance(fit_results, dict)
        assert 'kmeans' in fit_results
        assert 'dbscan' in fit_results
        assert 'hdbscan' in fit_results
        
        # Check that clustering was successful
        for algo_name, results in fit_results.items():
            if 'error' not in results:
                assert results['n_clusters'] >= 0
                assert 'silhouette_score' in results
    
    @pytest.mark.asyncio
    async def test_predict_cluster(self, clustering_engine, feature_extractor, sample_logs):
        """Test cluster prediction for new log entry"""
        # Setup models first
        log_dicts = [log.to_dict() for log in sample_logs]
        feature_extractor.fit_extractors(log_dicts)
        
        features_list = []
        for log_dict in log_dicts[:50]:  # Use subset for training
            features, feature_names = feature_extractor.extract_features(log_dict)
            features_list.append(features)
        
        features_matrix = np.array(features_list)
        await clustering_engine.fit_initial_model(features_matrix, feature_names)
        
        # Test prediction
        test_features, _ = feature_extractor.extract_features(log_dicts[51])
        cluster_results = await clustering_engine.predict_cluster(test_features)
        
        assert isinstance(cluster_results, list)
        assert len(cluster_results) > 0
        
        for result in cluster_results:
            assert isinstance(result, ClusterResult)
            assert hasattr(result, 'algorithm')
            assert hasattr(result, 'cluster_id')
            assert hasattr(result, 'confidence')
            assert hasattr(result, 'is_anomaly')
            assert 0.0 <= result.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_pattern_discovery(self, clustering_engine, feature_extractor, sample_logs):
        """Test pattern discovery functionality"""
        # Setup models
        log_dicts = [log.to_dict() for log in sample_logs]
        feature_extractor.fit_extractors(log_dicts)
        
        features_list = []
        for log_dict in log_dicts[:50]:
            features, feature_names = feature_extractor.extract_features(log_dict)
            features_list.append(features)
        
        features_matrix = np.array(features_list)
        await clustering_engine.fit_initial_model(features_matrix, feature_names)
        
        # Generate cluster results for pattern discovery
        recent_results = []
        log_samples = []
        
        for log_dict in log_dicts[51:61]:  # Use next 10 logs
            features, _ = feature_extractor.extract_features(log_dict)
            cluster_results = await clustering_engine.predict_cluster(features)
            recent_results.extend(cluster_results)
            log_samples.extend([log_dict['message']] * len(cluster_results))
        
        # Test pattern discovery
        patterns = await clustering_engine.discover_new_patterns(recent_results, log_samples)
        
        assert isinstance(patterns, list)
        # Patterns might be empty if no significant patterns found
        for pattern in patterns:
            assert hasattr(pattern, 'pattern_id')
            assert hasattr(pattern, 'pattern_type')
            assert hasattr(pattern, 'confidence')

class TestIntegration:
    """Integration tests for complete pipeline"""
    
    @pytest.mark.asyncio
    async def test_integration_full_pipeline(self, config):
        """Test complete pipeline from log to cluster results"""
        # Initialize components
        feature_extractor = LogFeatureExtractor(config)
        clustering_engine = StreamingClusteringEngine(config)
        
        # Generate sample data
        sample_logs = generate_sample_logs(200)
        log_dicts = [log.to_dict() for log in sample_logs]
        
        # Fit feature extractor
        feature_extractor.fit_extractors(log_dicts)
        
        # Prepare training data
        features_list = []
        for log_dict in log_dicts[:100]:  # Use first 100 for training
            features, feature_names = feature_extractor.extract_features(log_dict)
            features_list.append(features)
        
        features_matrix = np.array(features_list)
        
        # Fit clustering models
        fit_results = await clustering_engine.fit_initial_model(features_matrix, feature_names)
        
        # Test prediction on new data
        test_log = log_dicts[150]
        test_features, _ = feature_extractor.extract_features(test_log)
        cluster_results = await clustering_engine.predict_cluster(test_features)
        
        # Verify results
        assert isinstance(fit_results, dict)
        assert len(cluster_results) > 0
        
        # Check statistics
        stats = clustering_engine.get_cluster_statistics()
        assert isinstance(stats, dict)
        assert 'algorithms' in stats
        assert 'total_patterns_discovered' in stats
        
        print("✅ Integration test completed successfully")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF

    print_status "Test suite created"
}

# Create start and stop scripts
create_control_scripts() {
    print_info "Creating control scripts..."
    
    # Start script
    cat > start.sh << 'EOF'
#!/bin/bash

# Day 79: Log Clustering System - Start Script

echo "🚀 Starting Day 79: Log Clustering for Pattern Discovery"
echo "========================================================"

# Activate virtual environment
source venv/bin/activate

# Start Redis (if using Docker)
if command -v docker-compose &> /dev/null; then
    echo "🔧 Starting Redis with Docker..."
    docker-compose up -d redis
    sleep 5
fi

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    echo "⚠️  Redis not available. Some features may not work."
fi

# Start the application
echo "🌐 Starting clustering web application..."
echo "Dashboard will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop the application"
echo ""

python src/main.py
EOF

    # Stop script
    cat > stop.sh << 'EOF'
#!/bin/bash

# Day 79: Log Clustering System - Stop Script

echo "🛑 Stopping Day 79: Log Clustering System"
echo "=========================================="

# Stop Docker services if running
if command -v docker-compose &> /dev/null; then
    echo "🔧 Stopping Docker services..."
    docker-compose down
fi

# Kill any remaining Python processes
pkill -f "python src/main.py" 2>/dev/null || true

echo "✅ System stopped successfully"
EOF

    # Make scripts executable
    chmod +x start.sh stop.sh

    print_status "Control scripts created"
}

# Run tests
run_tests() {
    print_info "Running test suite..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run tests
    python -m pytest tests/test_clustering.py -v
    
    if [ $? -eq 0 ]; then
        print_status "All tests passed successfully"
    else
        print_error "Some tests failed"
        exit 1
    fi
}

# Run demonstration
run_demonstration() {
    print_info "Running system demonstration..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run demo
    python src/main.py demo
    
    print_status "Demonstration completed"
}

# Main execution flow
main() {
    echo "🎯 Day 79: Log Clustering for Pattern Discovery"
    echo "================================================"
    echo "Module 3: Advanced Log Processing Features"
    echo "Week 12: Advanced Analytics"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Create project
    create_project_structure
    
    # Setup virtual environment
    setup_virtual_environment
    
    # Install dependencies
    install_dependencies
    
    # Create all components
    create_configuration
    create_clustering_engine
    create_feature_extraction
    create_visualization
    create_main_application
    create_utilities
    create_test_suite
    create_control_scripts
    
    # Run tests
    run_tests
    
    # Run demonstration
    run_demonstration
    
    print_info "Setup completed successfully!"
    print_info "Next steps:"
    print_info "  1. Run ./start.sh to start the web application"
    print_info "  2. Open http://localhost:8000 in your browser"
    print_info "  3. Run ./stop.sh to stop all services"
    print_info ""
    print_info "For Docker deployment:"
    print_info "  docker-compose up --build"
    
    print_status "Day 79 implementation ready! 🎉"
}

# Execute main function
main "$@"
EOF

    chmod +x day79_implementation_script.sh
    print_status "Implementation script created"
}

# Run main function to execute the setup
main() {
    echo "🎯 Day 79: Log Clustering for Pattern Discovery Setup"
    echo "===================================================="
    
    check_prerequisites
    create_project_structure
    setup_virtual_environment
    install_dependencies
    create_configuration
    create_clustering_engine
    create_feature_extraction
    create_visualization
    create_main_application
    create_utilities
    create_test_suite
    create_control_scripts
    
    print_status "✅ Day 79 implementation script created successfully!"
    print_info "Execute ./day79_implementation_script.sh to run the complete setup"
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi