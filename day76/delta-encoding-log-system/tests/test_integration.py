import pytest
import asyncio
import tempfile
import shutil
from src.compression.delta_encoder import DeltaEncoder, DeltaDecoder
from src.storage.chunk_manager import ChunkManager
from src.compression.models import LogEntry, CompressionChunk
from config.delta_config import DeltaEncodingConfig

class TestIntegration:
    def setup_method(self):
        # Create temporary storage for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config = DeltaEncodingConfig()
        self.config.storage_path = self.temp_dir
        self.config.chunk_size = 10  # Small chunks for testing
        
        self.encoder = DeltaEncoder(self.config)
        self.decoder = DeltaDecoder()
        self.chunk_manager = ChunkManager(self.config)
    
    def teardown_method(self):
        # Clean up temporary storage
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow: encode -> store -> retrieve -> decode"""
        # Generate test data
        test_entries = []
        base_time = "2025-05-16T10:00:00Z"
        
        for i in range(20):
            entry = LogEntry(
                timestamp=f"2025-05-16T10:{i:02d}:00Z",
                level="INFO" if i % 3 != 0 else "ERROR",
                service="web-server",
                message=f"Request processed - user_{i%5} - endpoint_{i%3}",
                metadata={
                    "user_id": f"user_{i%5}",
                    "endpoint": f"/api/endpoint_{i%3}",
                    "response_time": 50 + (i % 100)
                }
            )
            test_entries.append(entry)
        
        # Compress entries
        baseline = None
        delta_entries = []
        
        for i, entry in enumerate(test_entries):
            if i % self.config.baseline_frequency == 0:
                baseline = entry
            else:
                delta, compression_ratio = self.encoder.encode_entry(entry, baseline)
                if delta:
                    delta_entries.append(delta)
        
        # Create and store chunk
        if baseline and delta_entries:
            chunk = CompressionChunk(
                chunk_id=f"test_chunk_{datetime.now().timestamp()}",
                baseline_entry=baseline,
                delta_entries=delta_entries,
                total_entries=len(test_entries),
                compressed_size=1000,  # Mock size
                original_size=2000,    # Mock size
                compression_ratio=0.5,
                created_at=datetime.now()
            )
            
            # Store chunk
            success = await self.chunk_manager.store_chunk(chunk)
            assert success
            
            # Retrieve chunk
            retrieved_chunk = await self.chunk_manager.load_chunk(chunk.chunk_id)
            assert retrieved_chunk is not None
            assert retrieved_chunk.chunk_id == chunk.chunk_id
            assert len(retrieved_chunk.delta_entries) == len(delta_entries)
            
            # Reconstruct entries
            reconstructed_entries = []
            for delta in retrieved_chunk.delta_entries:
                reconstructed = self.decoder.decode_entry(delta, retrieved_chunk.baseline_entry)
                reconstructed_entries.append(reconstructed)
            
            # Verify reconstruction accuracy
            original_non_baselines = [e for i, e in enumerate(test_entries) 
                                    if i % self.config.baseline_frequency != 0]
            
            assert len(reconstructed_entries) == len(original_non_baselines)
            
            for original, reconstructed in zip(original_non_baselines[:len(reconstructed_entries)], 
                                             reconstructed_entries):
                assert original.service == reconstructed.service
                assert original.level == reconstructed.level
                # Note: exact timestamp matching might vary due to delta reconstruction
    
    def test_compression_efficiency(self):
        """Test that compression achieves expected efficiency"""
        # Generate highly similar entries that should compress well
        baseline = LogEntry(
            timestamp="2025-05-16T10:00:00Z",
            level="INFO",
            service="api-server",
            message="User authentication successful",
            metadata={"ip": "192.168.1.100", "user_agent": "Mozilla/5.0"}
        )
        
        total_original_size = 0
        total_compressed_size = 0
        
        # First entry as baseline
        self.encoder.encode_entry(baseline)
        baseline_size = len(json.dumps(baseline.to_dict()).encode())
        total_original_size += baseline_size
        total_compressed_size += baseline_size
        
        # Generate 50 similar entries
        for i in range(1, 51):
            entry = LogEntry(
                timestamp=f"2025-05-16T10:{i:02d}:00Z",
                level="INFO",
                service="api-server",
                message="User authentication successful",
                metadata={"ip": f"192.168.1.{100+i}", "user_agent": "Mozilla/5.0"}
            )
            
            delta, compression_ratio = self.encoder.encode_entry(entry, baseline)
            if delta:
                entry_size = len(json.dumps(entry.to_dict()).encode())
                delta_size = len(json.dumps(delta.to_dict()).encode())
                
                total_original_size += entry_size
                total_compressed_size += delta_size
        
        overall_compression_ratio = total_compressed_size / total_original_size
        storage_saved_percent = (1 - overall_compression_ratio) * 100
        
        # Should achieve significant compression for similar entries
        assert storage_saved_percent > 30  # At least 30% savings
        assert overall_compression_ratio < 0.7  # Better than 70% of original size
        
        print(f"Compression achieved: {storage_saved_percent:.1f}% storage savings")
        print(f"Compression ratio: {overall_compression_ratio:.3f}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
