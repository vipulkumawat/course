import json
import asyncio
import logging
from typing import Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = logging.getLogger(__name__)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            self.logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

class ClusterWebSocketHandler:
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)

    async def handle_new_cluster(self, cluster_data: Dict[str, Any]):
        """Handle new cluster discovery and broadcast to clients"""
        message = {
            "type": "new_cluster",
            "data": cluster_data,
            "timestamp": cluster_data.get("timestamp")
        }
        
        await self.connection_manager.broadcast(json.dumps(message))
        self.logger.info(f"Broadcasted new cluster: {cluster_data.get('cluster_id', 'unknown')}")

    async def handle_anomaly_detection(self, anomaly_data: Dict[str, Any]):
        """Handle anomaly detection and send alerts"""
        message = {
            "type": "anomaly_alert",
            "data": anomaly_data,
            "severity": anomaly_data.get("severity", "medium"),
            "timestamp": anomaly_data.get("timestamp")
        }
        
        await self.connection_manager.broadcast(json.dumps(message))
        self.logger.warning(f"Broadcasted anomaly alert: {anomaly_data.get('pattern_type', 'unknown')}")

    async def handle_pattern_discovery(self, pattern_data: Dict[str, Any]):
        """Handle pattern discovery updates"""
        message = {
            "type": "pattern_discovery",
            "data": pattern_data,
            "timestamp": pattern_data.get("discovered_at")
        }
        
        await self.connection_manager.broadcast(json.dumps(message))
        self.logger.info(f"Broadcasted pattern discovery: {pattern_data.get('pattern_type', 'unknown')}")

    async def handle_cluster_stats_update(self, stats_data: Dict[str, Any]):
        """Handle cluster statistics updates"""
        message = {
            "type": "stats_update",
            "data": stats_data,
            "timestamp": stats_data.get("last_updated")
        }
        
        await self.connection_manager.broadcast(json.dumps(message))
