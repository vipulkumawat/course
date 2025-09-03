import hashlib
import json
from typing import Dict, Any, Optional
import redis.asyncio as redis
from sqlalchemy.orm import Session
from .models import FeatureFlag, Experiment, UserAssignment
from config.settings import settings

class FeatureFlagService:
    def __init__(self):
        self.redis_client = None
    
    async def initialize_redis(self):
        self.redis_client = redis.from_url(settings.redis_url)
    
    def _hash_user_experiment(self, user_id: str, experiment_id: int) -> float:
        """Generate deterministic hash for user-experiment combination"""
        combined = f"{user_id}-{experiment_id}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        hash_int = int.from_bytes(hash_bytes[:4], byteorder='big')
        return (hash_int % 10000) / 10000.0  # Return value between 0 and 1
    
    async def evaluate_feature_flag(self, flag_name: str, user_id: str, 
                                  user_attributes: Dict[str, Any] = None) -> bool:
        """Evaluate if feature flag is enabled for user"""
        # Try cache first
        cache_key = f"flag:{flag_name}:{user_id}"
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Get flag from database (in real implementation)
        # For demo, simulate flag evaluation
        user_hash = self._hash_user_experiment(user_id, hash(flag_name) % 1000)
        
        # Simple percentage rollout
        rollout_percentage = 0.1  # 10% rollout for demo
        is_enabled = user_hash < rollout_percentage
        
        # Cache result
        if self.redis_client:
            await self.redis_client.setex(
                cache_key, 
                settings.feature_flag_cache_ttl, 
                json.dumps(is_enabled)
            )
        
        return is_enabled
    
    async def assign_user_to_experiment(self, user_id: str, experiment_id: int, 
                                      db: Session) -> str:
        """Assign user to experiment variant"""
        # Check existing assignment
        existing = db.query(UserAssignment).filter(
            UserAssignment.user_id == user_id,
            UserAssignment.experiment_id == experiment_id
        ).first()
        
        if existing:
            return existing.variant
        
        # Generate new assignment
        user_hash = self._hash_user_experiment(user_id, experiment_id)
        variant = "treatment" if user_hash < 0.5 else "control"
        
        # Save assignment
        assignment = UserAssignment(
            user_id=user_id,
            experiment_id=experiment_id,
            variant=variant
        )
        db.add(assignment)
        db.commit()
        
        return variant
    
    async def get_experiment_results(self, experiment_id: int, 
                                   db: Session) -> Dict[str, Any]:
        """Get experiment results and statistical analysis"""
        # In real implementation, would query metrics
        return {
            "experiment_id": experiment_id,
            "total_users": 2000,
            "control_users": 1000,
            "treatment_users": 1000,
            "control_conversion": 0.12,
            "treatment_conversion": 0.15,
            "statistical_significance": 0.03,
            "confidence_interval": [0.01, 0.05],
            "recommendation": "Deploy treatment variant"
        }

feature_flag_service = FeatureFlagService()
