from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.user_data import UserDataMapping
import structlog

logger = structlog.get_logger()

class DataLineageTracker:
    def __init__(self, db: Session):
        self.db = db
    
    def track_user_data(self, user_id: str, data_type: str, 
                       storage_location: str, data_path: str, 
                       metadata: Optional[Dict] = None) -> UserDataMapping:
        """Track user data location in the system"""
        mapping = UserDataMapping(
            user_id=user_id,
            data_type=data_type,
            storage_location=storage_location,
            data_path=data_path,
            data_metadata=str(metadata) if metadata else None
        )
        
        self.db.add(mapping)
        self.db.commit()
        
        logger.info("User data tracked", 
                   user_id=user_id, 
                   data_type=data_type,
                   location=storage_location)
        
        return mapping
    
    def get_user_data_locations(self, user_id: str) -> List[UserDataMapping]:
        """Get all data locations for a user"""
        return self.db.query(UserDataMapping).filter(
            UserDataMapping.user_id == user_id
        ).all()
    
    def remove_user_data_mapping(self, user_id: str, data_location: str):
        """Remove data mapping after successful erasure"""
        self.db.query(UserDataMapping).filter(
            UserDataMapping.user_id == user_id,
            UserDataMapping.storage_location == data_location
        ).delete()
        self.db.commit()
    
    def get_data_statistics(self) -> Dict:
        """Get data tracking statistics"""
        total_mappings = self.db.query(UserDataMapping).count()
        unique_users = self.db.query(UserDataMapping.user_id).distinct().count()
        
        return {
            "total_mappings": total_mappings,
            "unique_users": unique_users,
            "data_types": self._get_data_type_counts()
        }
    
    def _get_data_type_counts(self) -> Dict:
        """Get count of each data type"""
        results = self.db.query(
            UserDataMapping.data_type,
            func.count(UserDataMapping.id).label('count')
        ).group_by(UserDataMapping.data_type).all()
        
        return {result.data_type: result.count for result in results}
