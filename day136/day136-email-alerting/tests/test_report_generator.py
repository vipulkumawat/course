import pytest
from unittest.mock import Mock, patch
from src.reports.report_generator import ReportGenerator, ReportConfig

@pytest.fixture
def report_generator():
    mock_redis = Mock()
    return ReportGenerator(mock_redis)

@pytest.fixture
def sample_config():
    return ReportConfig(
        title="Test Report",
        description="Test description",
        metrics=["requests_per_second", "error_rate"],
        time_range_hours=24
    )

@pytest.mark.asyncio
async def test_generate_daily_report(report_generator, sample_config):
    """Test daily report generation"""
    with patch.object(report_generator, '_fetch_metrics_data') as mock_fetch, \
         patch.object(report_generator, '_generate_charts') as mock_charts:
        
        mock_fetch.return_value = {
            "requests_per_second": [{"timestamp": "2025-06-16T10:00:00", "value": 100.0}],
            "error_rate": [{"timestamp": "2025-06-16T10:00:00", "value": 2.0}]
        }
        mock_charts.return_value = {"line_chart": "base64_data"}
        
        report = await report_generator.generate_daily_report(sample_config)
        
        assert report["title"] == "Test Report"
        assert report["description"] == "Test description"
        assert "metrics" in report
        assert "charts" in report
        assert "summary" in report
        assert "recommendations" in report

def test_calculate_statistics(report_generator):
    """Test statistics calculation"""
    metrics_data = {
        "requests_per_second": [
            {"timestamp": "2025-06-16T10:00:00", "value": 100.0},
            {"timestamp": "2025-06-16T10:15:00", "value": 150.0},
            {"timestamp": "2025-06-16T10:30:00", "value": 120.0}
        ]
    }
    
    stats = report_generator._calculate_statistics(metrics_data)
    
    assert "requests_per_second" in stats
    assert stats["requests_per_second"]["count"] == 3
    assert stats["requests_per_second"]["min"] == 100.0
    assert stats["requests_per_second"]["max"] == 150.0
    assert stats["requests_per_second"]["average"] == pytest.approx(123.33, rel=1e-2)

def test_generate_summary(report_generator):
    """Test summary generation"""
    stats = {
        "error_rate": {"average": 2.5},
        "response_time_ms": {"average": 150.0}
    }
    
    summary = report_generator._generate_summary(stats)
    
    assert "Error Rate" in summary
    assert "Response Time Ms" in summary
    assert isinstance(summary, str)
    assert len(summary) > 0
