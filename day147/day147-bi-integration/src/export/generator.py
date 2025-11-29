import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datetime import datetime
import json
from typing import List
from src.models import ExportRequest, ExportMetadata
from src.query.influx_builder import InfluxQueryBuilder
from config.settings import settings
import uuid

class ExportGenerator:
    def __init__(self):
        self.query_builder = InfluxQueryBuilder()
        self.export_base_path = Path(settings.EXPORT_BASE_PATH)
        self.export_base_path.mkdir(parents=True, exist_ok=True)
    
    def generate_export(self, request: ExportRequest) -> ExportMetadata:
        """Generate data export in requested format"""
        export_id = str(uuid.uuid4())[:8]
        
        # Query data from InfluxDB
        data = self._fetch_export_data(request)
        
        # Handle empty data
        if data.empty:
            # Create empty DataFrame with expected columns
            data = pd.DataFrame(columns=['timestamp', 'service', 'endpoint', 'value'])
        
        # Generate export file
        if request.format == "csv":
            file_path = self._generate_csv(data, request.date, export_id)
        else:  # parquet
            file_path = self._generate_parquet(data, request.date, export_id)
        
        # Create metadata (file should exist now)
        file_stat = file_path.stat()
        metadata = ExportMetadata(
            export_id=export_id,
            date=request.date,
            format=request.format,
            url=f"/exports/{file_path.relative_to(self.export_base_path)}",
            row_count=len(data),
            file_size_bytes=file_stat.st_size,
            columns=list(data.columns) if not data.empty else [],
            generated_at=datetime.utcnow()
        )
        
        # Save metadata
        self._save_metadata(metadata)
        
        return metadata
    
    def _fetch_export_data(self, request: ExportRequest) -> pd.DataFrame:
        """Fetch data for export from InfluxDB"""
        from src.models import MetricQuery, TimeRange, AggregationWindow
        
        try:
            # Build query for entire day
            query = MetricQuery(
                measurement="http_requests",
                time_range=TimeRange(
                    start=request.date,
                    end=request.date.replace(hour=23, minute=59, second=59)
                ),
                aggregation_window=AggregationWindow.HOUR,
                filters={"service": request.services} if request.services else {},
                page_size=100000
            )
            
            response = self.query_builder.execute_query(query)
            
            # Handle empty response
            if not response.data:
                return pd.DataFrame()
            
            df = pd.DataFrame(response.data)
            
            # Add business metrics
            if not df.empty:
                df['error_rate'] = 0.0  # Calculate from actual data
                df['requests_per_second'] = df['value'] / 3600  # Hourly to per-second
            
            return df
        except Exception as e:
            # Log error and return empty DataFrame
            import logging
            logging.error(f"Error fetching export data: {e}")
            return pd.DataFrame()
    
    def _generate_csv(self, data: pd.DataFrame, date: datetime, export_id: str) -> Path:
        """Generate CSV export"""
        year_month_day = date.strftime("%Y/%m/%d")
        export_dir = self.export_base_path / "csv" / year_month_day
        export_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = export_dir / f"metrics_{export_id}.csv"
        
        # Write CSV (even if empty)
        if data.empty:
            # Create empty CSV with headers if we have column info
            file_path.write_text("timestamp,service,endpoint,value\n")
        else:
            data.to_csv(file_path, index=False)
        
        return file_path
    
    def _generate_parquet(self, data: pd.DataFrame, date: datetime, export_id: str) -> Path:
        """Generate Parquet export"""
        year_month_day = date.strftime("%Y/%m/%d")
        export_dir = self.export_base_path / "parquet" / year_month_day
        export_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = export_dir / f"metrics_{export_id}.parquet"
        
        # Write Parquet (even if empty)
        if data.empty:
            # Create empty parquet with schema
            schema = pa.schema([
                pa.field('timestamp', pa.string()),
                pa.field('service', pa.string()),
                pa.field('endpoint', pa.string()),
                pa.field('value', pa.float64())
            ])
            table = pa.Table.from_pylist([], schema=schema)
        else:
            table = pa.Table.from_pandas(data)
        
        pq.write_table(table, file_path, compression='snappy')
        
        return file_path
    
    def _save_metadata(self, metadata: ExportMetadata):
        """Save export metadata"""
        manifest_path = self.export_base_path / "manifest.json"
        
        # Load existing manifest
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
        else:
            manifest = {"exports": []}
        
        # Add new export
        manifest["exports"].append(metadata.model_dump(mode='json'))
        
        # Keep only last 100 exports
        manifest["exports"] = manifest["exports"][-100:]
        
        # Save manifest
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2, default=str)
    
    def get_manifest(self) -> dict:
        """Get export manifest"""
        manifest_path = self.export_base_path / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                return json.load(f)
        return {"exports": []}
