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
