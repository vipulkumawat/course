from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from ..models.user import UserPreference, PreferenceTemplate
import json
import redis
from datetime import datetime, timedelta

class PreferenceService:
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
        self.cache_ttl = 3600  # 1 hour
    
    async def get_user_preferences(self, user_id: int, category: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve user preferences with Redis caching"""
        cache_key = f"preferences:{user_id}:{category or 'all'}"
        
        # Try Redis cache first
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Query database
        query = self.db.query(UserPreference).filter(UserPreference.user_id == user_id)
        if category:
            query = query.filter(UserPreference.category == category)
        
        preferences = query.all()
        result = {}
        
        for pref in preferences:
            if pref.category not in result:
                result[pref.category] = {}
            result[pref.category][pref.key] = pref.value
        
        # Cache result
        self.redis.setex(cache_key, self.cache_ttl, json.dumps(result))
        return result
    
    async def update_preference(self, user_id: int, category: str, key: str, value: Any) -> bool:
        """Update or create user preference"""
        try:
            # Check if preference exists
            existing = self.db.query(UserPreference).filter(
                UserPreference.user_id == user_id,
                UserPreference.category == category,
                UserPreference.key == key
            ).first()
            
            if existing:
                existing.value = value
                existing.updated_at = datetime.utcnow()
            else:
                new_pref = UserPreference(
                    user_id=user_id,
                    category=category,
                    key=key,
                    value=value
                )
                self.db.add(new_pref)
            
            self.db.commit()
            
            # Invalidate cache
            cache_pattern = f"preferences:{user_id}:*"
            for key in self.redis.scan_iter(match=cache_pattern):
                self.redis.delete(key)
            
            return True
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def bulk_update_preferences(self, user_id: int, preferences: Dict[str, Dict[str, Any]]) -> bool:
        """Bulk update multiple preferences"""
        try:
            for category, prefs in preferences.items():
                for key, value in prefs.items():
                    existing = self.db.query(UserPreference).filter(
                        UserPreference.user_id == user_id,
                        UserPreference.category == category,
                        UserPreference.key == key
                    ).first()
                    
                    if existing:
                        existing.value = value
                        existing.updated_at = datetime.utcnow()
                    else:
                        new_pref = UserPreference(
                            user_id=user_id,
                            category=category,
                            key=key,
                            value=value
                        )
                        self.db.add(new_pref)
            
            self.db.commit()
            
            # Invalidate cache
            cache_pattern = f"preferences:{user_id}:*"
            for key in self.redis.scan_iter(match=cache_pattern):
                self.redis.delete(key)
            
            return True
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def get_default_preferences(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get system default preferences"""
        query = self.db.query(PreferenceTemplate).filter(
            PreferenceTemplate.is_system_default == True
        )
        if category:
            query = query.filter(PreferenceTemplate.category == category)
        
        templates = query.all()
        result = {}
        
        for template in templates:
            if template.category not in result:
                result[template.category] = {}
            result[template.category].update(template.template_data)
        
        return result
