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
