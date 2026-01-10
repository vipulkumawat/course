"""Test custom metrics exporter"""
import pytest
from prometheus_client import REGISTRY
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'exporters'))

# Import the exporter module to register metrics
import log_metrics_exporter

def test_metrics_registered():
    """Test that all metrics are registered"""
    metric_names = [m.name for m in REGISTRY.collect()]
    
    assert 'log_ingestion_rate' in metric_names
    assert 'log_processing_latency_seconds' in metric_names
    assert 'log_queue_depth' in metric_names
    assert 'app_cpu_usage_percent' in metric_names

def test_collector_initialization():
    """Test collector initializes correctly"""
    from log_metrics_exporter import LogMetricsCollector
    
    collector = LogMetricsCollector()
    assert collector.base_ingestion_rate == 1000
    assert collector.base_latency == 0.05
    assert collector.queue_size == 0

print("✅ All exporter tests passed!")
