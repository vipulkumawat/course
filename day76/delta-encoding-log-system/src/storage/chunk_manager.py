import os
import json
import pickle
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import aiofiles
from src.compression.models import LogEntry, DeltaEntry, CompressionChunk

class ChunkManager:
    def __init__(self, config):
        self.config = config
        self.storage_path = config.storage_path
        self.chunks: Dict[str, CompressionChunk] = {}
        self.current_chunk: Optional[CompressionChunk] = None
        
        # Ensure storage directories exist
        os.makedirs(self.storage_path, exist_ok=True)
        os.makedirs(config.backup_path, exist_ok=True)
    
    async def store_chunk(self, chunk: CompressionChunk) -> bool:
        """Store compression chunk to disk"""
        try:
            chunk_file = os.path.join(self.storage_path, f"{chunk.chunk_id}.chunk")
            
            # Serialize chunk data
            chunk_data = {
                'chunk_id': chunk.chunk_id,
                'baseline_entry': chunk.baseline_entry.to_dict(),
                'delta_entries': [delta.to_dict() for delta in chunk.delta_entries],
                'total_entries': chunk.total_entries,
                'compressed_size': chunk.compressed_size,
                'original_size': chunk.original_size,
                'compression_ratio': chunk.compression_ratio,
                'created_at': chunk.created_at.isoformat()
            }
            
            async with aiofiles.open(chunk_file, 'w') as f:
                await f.write(json.dumps(chunk_data, indent=2))
            
            # Update in-memory index
            self.chunks[chunk.chunk_id] = chunk
            
            return True
        except Exception as e:
            print(f"Error storing chunk {chunk.chunk_id}: {e}")
            return False
    
    async def load_chunk(self, chunk_id: str) -> Optional[CompressionChunk]:
        """Load compression chunk from disk"""
        if chunk_id in self.chunks:
            return self.chunks[chunk_id]
        
        try:
            chunk_file = os.path.join(self.storage_path, f"{chunk_id}.chunk")
            if not os.path.exists(chunk_file):
                return None
            
            async with aiofiles.open(chunk_file, 'r') as f:
                chunk_data = json.loads(await f.read())
            
            # Reconstruct chunk object
            baseline = LogEntry.from_dict(chunk_data['baseline_entry'])
            deltas = [DeltaEntry(**delta) for delta in chunk_data['delta_entries']]
            
            chunk = CompressionChunk(
                chunk_id=chunk_data['chunk_id'],
                baseline_entry=baseline,
                delta_entries=deltas,
                total_entries=chunk_data['total_entries'],
                compressed_size=chunk_data['compressed_size'],
                original_size=chunk_data['original_size'],
                compression_ratio=chunk_data['compression_ratio'],
                created_at=datetime.fromisoformat(chunk_data['created_at'])
            )
            
            self.chunks[chunk_id] = chunk
            return chunk
            
        except Exception as e:
            print(f"Error loading chunk {chunk_id}: {e}")
            return None
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        total_chunks = len(self.chunks)
        total_entries = sum(chunk.total_entries for chunk in self.chunks.values())
        total_compressed_size = sum(chunk.compressed_size for chunk in self.chunks.values())
        total_original_size = sum(chunk.original_size for chunk in self.chunks.values())
        
        avg_compression = (
            (total_original_size - total_compressed_size) / total_original_size * 100
            if total_original_size > 0 else 0
        )
        
        return {
            'total_chunks': total_chunks,
            'total_entries': total_entries,
            'compressed_size_mb': total_compressed_size / (1024 * 1024),
            'original_size_mb': total_original_size / (1024 * 1024),
            'storage_savings_percent': avg_compression,
            'avg_entries_per_chunk': total_entries / total_chunks if total_chunks > 0 else 0
        }
    
    async def cleanup_old_chunks(self, days_old: int = 30):
        """Clean up chunks older than specified days"""
        cutoff_date = datetime.now() - pd.Timedelta(days=days_old)
        
        chunks_to_remove = [
            chunk_id for chunk_id, chunk in self.chunks.items()
            if chunk.created_at < cutoff_date
        ]
        
        for chunk_id in chunks_to_remove:
            try:
                chunk_file = os.path.join(self.storage_path, f"{chunk_id}.chunk")
                if os.path.exists(chunk_file):
                    os.remove(chunk_file)
                del self.chunks[chunk_id]
            except Exception as e:
                print(f"Error removing chunk {chunk_id}: {e}")
        
        return len(chunks_to_remove)
