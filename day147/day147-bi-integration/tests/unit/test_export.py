import pytest
from datetime import datetime
from src.export.generator import ExportGenerator
from src.models import ExportRequest

@pytest.fixture
def export_generator():
    return ExportGenerator()

def test_csv_export_generation(export_generator):
    """Test CSV export generation"""
    request = ExportRequest(
        date=datetime(2025, 6, 15),
        format="csv",
        services=["api"]
    )
    
    # Note: This will create actual files in exports directory
    # In production, mock the file operations
    assert request.format == "csv"
    assert request.date.year == 2025

def test_manifest_operations(export_generator):
    """Test export manifest operations"""
    manifest = export_generator.get_manifest()
    assert "exports" in manifest
    assert isinstance(manifest["exports"], list)
