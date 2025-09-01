from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from ..services.preference_service import PreferenceService
from ...database.connection import get_db
from ...auth.dependencies import get_current_user
from pydantic import BaseModel
import json
import redis

router = APIRouter()

# Pydantic models
class PreferenceUpdate(BaseModel):
    category: str
    key: str
    value: Any

class BulkPreferenceUpdate(BaseModel):
    preferences: Dict[str, Dict[str, Any]]

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_preference_update(self, user_id: int, data: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id][:]:
                try:
                    await connection.send_text(json.dumps(data))
                except:
                    self.active_connections[user_id].remove(connection)

manager = ConnectionManager()

def get_preference_service(db: Session = Depends(get_db)) -> PreferenceService:
    redis_client = redis.from_url("redis://localhost:6379/0")
    return PreferenceService(db, redis_client)

@router.get("/preferences")
async def get_preferences(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    preference_service: PreferenceService = Depends(get_preference_service)
):
    """Get user preferences"""
    try:
        preferences = await preference_service.get_user_preferences(
            current_user["id"], category
        )
        return {"preferences": preferences}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving preferences: {str(e)}"
        )

@router.put("/preferences")
async def update_preference(
    preference_update: PreferenceUpdate,
    current_user: dict = Depends(get_current_user),
    preference_service: PreferenceService = Depends(get_preference_service)
):
    """Update single preference"""
    try:
        success = await preference_service.update_preference(
            current_user["id"],
            preference_update.category,
            preference_update.key,
            preference_update.value
        )
        
        if success:
            # Notify other sessions via WebSocket
            await manager.send_preference_update(current_user["id"], {
                "type": "preference_updated",
                "category": preference_update.category,
                "key": preference_update.key,
                "value": preference_update.value
            })
            
            return {"success": True, "message": "Preference updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update preference"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating preference: {str(e)}"
        )

@router.put("/preferences/bulk")
async def bulk_update_preferences(
    bulk_update: BulkPreferenceUpdate,
    current_user: dict = Depends(get_current_user),
    preference_service: PreferenceService = Depends(get_preference_service)
):
    """Bulk update preferences"""
    try:
        success = await preference_service.bulk_update_preferences(
            current_user["id"],
            bulk_update.preferences
        )
        
        if success:
            # Notify other sessions
            await manager.send_preference_update(current_user["id"], {
                "type": "preferences_bulk_updated",
                "preferences": bulk_update.preferences
            })
            
            return {"success": True, "message": "Preferences updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update preferences"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating preferences: {str(e)}"
        )

@router.get("/preferences/defaults")
async def get_default_preferences(
    category: Optional[str] = None,
    preference_service: PreferenceService = Depends(get_preference_service)
):
    """Get system default preferences"""
    try:
        defaults = await preference_service.get_default_preferences(category)
        return {"defaults": defaults}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving default preferences: {str(e)}"
        )

@router.websocket("/ws/preferences/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle any incoming WebSocket messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
