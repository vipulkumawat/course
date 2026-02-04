"""
Comprehensive test suite for impact analyzer
"""
import pytest
import networkx as nx
from src.impact_analyzer import ImpactAnalyzer, ChangeProposal, create_sample_dependency_graph

@pytest.fixture
def analyzer():
    graph, metadata = create_sample_dependency_graph()
    return ImpactAnalyzer(graph, metadata)

def test_analyzer_initialization(analyzer):
    """Test analyzer initializes correctly"""
    assert analyzer is not None
    assert len(analyzer.graph.nodes) > 0
    assert len(analyzer.metadata) > 0

def test_direct_impact_calculation(analyzer):
    """Test direct impact on immediate dependencies"""
    proposal = ChangeProposal(
        change_type='api_modification',
        target_service='log-enrichment',
        change_description='Add new API endpoint'
    )
    
    result = analyzer.analyze_change(proposal)
    
    assert result.blast_radius > 0
    assert 'log-enrichment' in result.affected_services
    assert result.risk_score >= 0 and result.risk_score <= 100

def test_transitive_dependencies(analyzer):
    """Test transitive dependency traversal"""
    proposal = ChangeProposal(
        change_type='infrastructure',
        target_service='rabbitmq-cluster',
        change_description='Upgrade RabbitMQ version'
    )
    
    result = analyzer.analyze_change(proposal)
    
    # RabbitMQ should affect multiple downstream services
    assert result.blast_radius >= 3
    assert 'rabbitmq-cluster' in result.affected_services

def test_critical_path_detection(analyzer):
    """Test critical path identification"""
    proposal = ChangeProposal(
        change_type='schema_change',
        target_service='log-collector',
        change_description='Change log format'
    )
    
    result = analyzer.analyze_change(proposal)
    
    # log-collector is critical
    assert result.critical_path == True

def test_risk_score_calculation(analyzer):
    """Test risk score is calculated properly"""
    # High risk change
    high_risk = ChangeProposal(
        change_type='schema_change',
        target_service='rabbitmq-cluster',
        change_description='Breaking schema change'
    )
    
    high_result = analyzer.analyze_change(high_risk)
    
    # Low risk change
    low_risk = ChangeProposal(
        change_type='configuration',
        target_service='reporting-service',
        change_description='Update config parameter'
    )
    
    low_result = analyzer.analyze_change(low_risk)
    
    assert high_result.risk_score > low_result.risk_score

def test_recommendations_generation(analyzer):
    """Test that recommendations are generated"""
    proposal = ChangeProposal(
        change_type='infrastructure',
        target_service='elasticsearch-cluster',
        change_description='Scale cluster'
    )
    
    result = analyzer.analyze_change(proposal)
    
    assert len(result.recommendations) > 0
    assert isinstance(result.recommendations[0], str)

def test_blast_radius_accuracy(analyzer):
    """Test blast radius calculation accuracy"""
    # Service with many dependencies
    proposal = ChangeProposal(
        change_type='api_modification',
        target_service='log-processor',
        change_description='Update API'
    )
    
    result = analyzer.analyze_change(proposal)
    
    # Verify all affected services are actually in dependency tree
    for service in result.affected_services:
        assert service in analyzer.graph.nodes

def test_caching_mechanism(analyzer):
    """Test that analysis results are cached"""
    proposal = ChangeProposal(
        change_type='api_modification',
        target_service='log-enrichment',
        change_description='Test caching'
    )
    
    # First analysis
    result1 = analyzer.analyze_change(proposal)
    cache_size_before = len(analyzer.analysis_cache)
    
    # Second analysis (should use cache)
    result2 = analyzer.analyze_change(proposal)
    cache_size_after = len(analyzer.analysis_cache)
    
    assert result1.risk_score == result2.risk_score
    assert cache_size_before == cache_size_after

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
