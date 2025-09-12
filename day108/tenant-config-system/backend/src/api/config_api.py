from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Optional
from services.config_service import config_service
from models.tenant_config import ConfigChange
import json
import structlog

logger = structlog.get_logger()
router = APIRouter()

# WebSocket connection manager
class ConfigWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, tenant_id: str):
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = []
        self.active_connections[tenant_id].append(websocket)
        
        # Subscribe to config changes for this tenant
        await config_service.subscribe_to_changes(
            tenant_id, 
            lambda tid, keys: self.broadcast_to_tenant(tid, {"type": "config_update", "keys": keys})
        )
    
    def disconnect(self, websocket: WebSocket, tenant_id: str):
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].remove(websocket)
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
    
    async def broadcast_to_tenant(self, tenant_id: str, message: dict):
        if tenant_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[tenant_id]:
                try:
                    await connection.send_json(message)
                except:
                    dead_connections.append(connection)
            
            # Clean up dead connections
            for conn in dead_connections:
                self.active_connections[tenant_id].remove(conn)

websocket_manager = ConfigWebSocketManager()

@router.get("/config/{tenant_id}")
async def get_tenant_config(tenant_id: str, config_key: Optional[str] = None):
    """Get tenant configuration"""
    try:
        config = await config_service.get_tenant_config(tenant_id, config_key)
        return {"success": True, "data": config}
    except Exception as e:
        logger.error("Failed to get config", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config/{tenant_id}")
async def update_tenant_config(tenant_id: str, updates: Dict[str, Any], updated_by: str = "admin"):
    """Update tenant configuration"""
    try:
        success = await config_service.update_tenant_config(tenant_id, updates, updated_by)
        if success:
            return {"success": True, "message": "Configuration updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update configuration")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to update config", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/{tenant_id}/history")
async def get_config_history(tenant_id: str, limit: int = 10):
    """Get configuration change history"""
    try:
        history = await config_service.get_config_history(tenant_id, limit)
        return {"success": True, "data": [change.dict() for change in history]}
    except Exception as e:
        logger.error("Failed to get config history", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/{tenant_id}/validate")
async def validate_config(tenant_id: str, config_data: Dict[str, Any]):
    """Validate configuration data"""
    try:
        is_valid = await config_service.validate_config(config_data)
        return {"success": True, "valid": is_valid}
    except Exception as e:
        logger.error("Failed to validate config", tenant_id=tenant_id, error=str(e))
        return {"success": True, "valid": False, "error": str(e)}

@router.delete("/config/{tenant_id}")
async def reset_tenant_config(tenant_id: str, reset_by: str = "admin"):
    """Reset tenant configuration to defaults"""
    try:
        success = await config_service.reset_tenant_config(tenant_id, reset_by)
        return {"success": success, "message": "Configuration reset to defaults"}
    except Exception as e:
        logger.error("Failed to reset config", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/config/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
    """WebSocket endpoint for real-time configuration updates"""
    await websocket_manager.connect(websocket, tenant_id)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, tenant_id)
