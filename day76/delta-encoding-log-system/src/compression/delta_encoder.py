import json
import lz4.frame
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
from .models import LogEntry, DeltaEntry, CompressionChunk

class DeltaEncoder:
    def __init__(self, config):
        self.config = config
        self.baselines: Dict[str, LogEntry] = {}
        self.compression_stats = {
            'total_entries': 0,
            'compressed_entries': 0,
            'storage_saved': 0,
            'avg_compression_ratio': 0.0
        }
    
    def encode_entry(self, entry: LogEntry, baseline: Optional[LogEntry] = None) -> Tuple[DeltaEntry, float]:
        """Encode a log entry as delta from baseline"""
        if baseline is None:
            # First entry becomes baseline
            self.baselines[entry.service] = entry
            return None, 0.0
        
        # Calculate field-level deltas
        field_deltas = self._calculate_field_deltas(entry, baseline)
        
        # Only create delta if it's actually smaller
        original_size = len(json.dumps(entry.to_dict()).encode())
        delta_size = len(json.dumps(field_deltas).encode())
        
        if delta_size >= original_size:
            # Delta is not beneficial, return None
            return None, 1.0
        
        # Compress delta data
        compressed_deltas = self._compress_deltas(field_deltas)
        
        # Calculate final compression ratio
        compressed_size = len(json.dumps(compressed_deltas).encode())
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        
        # Only use compressed delta if it's actually smaller
        if compressed_size >= original_size:
            return None, 1.0
        
        delta_entry = DeltaEntry(
            entry_id=entry.entry_id,
            baseline_id=baseline.entry_id,
            field_deltas=compressed_deltas,
            compression_ratio=compression_ratio,
            created_at=datetime.now()
        )
        
        self._update_stats(compression_ratio)
        return delta_entry, compression_ratio
    
    def _calculate_field_deltas(self, entry: LogEntry, baseline: LogEntry) -> Dict[str, Any]:
        """Calculate differences between entry and baseline"""
        deltas = {}
        entry_dict = entry.to_dict()
        baseline_dict = baseline.to_dict()
        
        for field, value in entry_dict.items():
            baseline_value = baseline_dict.get(field)
            
            if field == 'timestamp':
                # Store timestamp delta in seconds (simpler)
                entry_time = datetime.fromisoformat(value.replace('Z', '+00:00'))
                baseline_time = datetime.fromisoformat(baseline_value.replace('Z', '+00:00'))
                delta_sec = int((entry_time - baseline_time).total_seconds())
                if delta_sec != 0:
                    deltas[field] = delta_sec
            
            elif field == 'metadata':
                # Only store changed metadata fields
                metadata_deltas = {}
                for meta_key, meta_value in value.items():
                    baseline_meta = baseline_value.get(meta_key)
                    if meta_value != baseline_meta:
                        metadata_deltas[meta_key] = meta_value
                if metadata_deltas:
                    deltas[field] = metadata_deltas
            
            elif value != baseline_value:
                # Store only changed values
                deltas[field] = value
        
        return deltas
    
    def _find_common_prefix(self, str1: str, str2: str) -> str:
        """Find common prefix between two strings"""
        common = ""
        for i in range(min(len(str1), len(str2))):
            if str1[i] == str2[i]:
                common += str1[i]
            else:
                break
        return common
    
    def _find_common_suffix(self, str1: str, str2: str) -> str:
        """Find common suffix between two strings"""
        common = ""
        for i in range(1, min(len(str1), len(str2)) + 1):
            if str1[-i] == str2[-i]:
                common = str1[-i] + common
            else:
                break
        return common
    
    def _compress_deltas(self, deltas: Dict[str, Any]) -> Dict[str, Any]:
        """Apply additional compression to delta data"""
        # Convert to JSON and compress with LZ4
        json_data = json.dumps(deltas, separators=(',', ':')).encode()
        compressed = lz4.frame.compress(json_data)
        
        # Return base64 encoded compressed data if it's smaller
        if len(compressed) < len(json_data):
            import base64
            return {
                'compressed': True,
                'data': base64.b64encode(compressed).decode(),
                'original_size': len(json_data)
            }
        else:
            return deltas
    
    def _update_stats(self, compression_ratio: float):
        """Update compression statistics"""
        self.compression_stats['total_entries'] += 1
        self.compression_stats['compressed_entries'] += 1
        
        # Update running average
        total = self.compression_stats['compressed_entries']
        current_avg = self.compression_stats['avg_compression_ratio']
        self.compression_stats['avg_compression_ratio'] = (
            (current_avg * (total - 1) + compression_ratio) / total
        )
        
        self.compression_stats['storage_saved'] += (1 - compression_ratio) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        return self.compression_stats.copy()

class DeltaDecoder:
    def __init__(self):
        self.reconstruction_cache = {}
    
    def decode_entry(self, delta_entry: DeltaEntry, baseline: LogEntry) -> LogEntry:
        """Reconstruct original log entry from delta and baseline"""
        # Check cache first
        cache_key = f"{delta_entry.entry_id}:{baseline.entry_id}"
        if cache_key in self.reconstruction_cache:
            return self.reconstruction_cache[cache_key]
        
        # Decompress deltas if needed
        field_deltas = self._decompress_deltas(delta_entry.field_deltas)
        
        # Reconstruct entry
        reconstructed = baseline.to_dict().copy()
        
        for field, delta_value in field_deltas.items():
            if field == 'timestamp':
                # Reconstruct timestamp
                baseline_time = datetime.fromisoformat(baseline.timestamp.replace('Z', '+00:00'))
                from datetime import timedelta
                new_time = baseline_time + timedelta(seconds=delta_value)
                reconstructed[field] = new_time.isoformat() + 'Z'
            
            elif field == 'metadata':
                # Merge metadata
                baseline_metadata = getattr(baseline, 'metadata', {})
                reconstructed[field] = {**baseline_metadata, **delta_value}
            
            else:
                # Direct value replacement
                reconstructed[field] = delta_value
        
        result = LogEntry.from_dict(reconstructed)
        
        # Cache result
        self.reconstruction_cache[cache_key] = result
        if len(self.reconstruction_cache) > 1000:  # LRU-like cleanup
            oldest_key = next(iter(self.reconstruction_cache))
            del self.reconstruction_cache[oldest_key]
        
        return result
    
    def _decompress_deltas(self, deltas: Dict[str, Any]) -> Dict[str, Any]:
        """Decompress delta data if compressed"""
        if deltas.get('compressed'):
            import base64
            compressed_data = base64.b64decode(deltas['data'])
            decompressed = lz4.frame.decompress(compressed_data)
            return json.loads(decompressed.decode())
        return deltas
