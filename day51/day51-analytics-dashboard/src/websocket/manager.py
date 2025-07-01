import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass
import uuid

@dataclass
class ClientConnection:
    websocket: WebSocket
    client_id: str
    subscriptions: Set[str]
    connected_at: datetime
    last_heartbeat: datetime

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, ClientConnection] = {}
        self.logger = logging.getLogger(__name__)
        self.heartbeat_task = None
        
    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        client_id = str(uuid.uuid4())
        now = datetime.now()
        connection = ClientConnection(
            websocket=websocket,
            client_id=client_id,
            subscriptions=set(),
            connected_at=now,
            last_heartbeat=now
        )
        self.active_connections[client_id] = connection
        self.logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        if len(self.active_connections) == 1 and not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        return client_id
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
            if not self.active_connections and self.heartbeat_task:
                self.heartbeat_task.cancel()
                self.heartbeat_task = None
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        if client_id not in self.active_connections:
            return False
        connection = self.active_connections[client_id]
        try:
            await connection.websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            self.logger.error(f"Error sending message to {client_id}: {e}")
            self.disconnect(client_id)
            return False
    
    async def broadcast(self, message: Dict[str, Any], subscription_filter: Optional[str] = None):
        if not self.active_connections:
            return
        disconnect_clients = []
        for client_id, connection in self.active_connections.items():
            if subscription_filter and subscription_filter not in connection.subscriptions:
                continue
            try:
                await connection.websocket.send_text(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnect_clients.append(client_id)
        for client_id in disconnect_clients:
            self.disconnect(client_id)
    
    async def subscribe(self, client_id: str, subscription: str) -> bool:
        if client_id not in self.active_connections:
            return False
        self.active_connections[client_id].subscriptions.add(subscription)
        self.logger.info(f"Client {client_id} subscribed to {subscription}")
        return True
    
    async def unsubscribe(self, client_id: str, subscription: str) -> bool:
        if client_id not in self.active_connections:
            return False
        self.active_connections[client_id].subscriptions.discard(subscription)
        self.logger.info(f"Client {client_id} unsubscribed from {subscription}")
        return True
    
    async def handle_client_message(self, client_id: str, message: Dict[str, Any]):
        message_type = message.get('type')
        if message_type == 'heartbeat':
            if client_id in self.active_connections:
                self.active_connections[client_id].last_heartbeat = datetime.now()
                await self.send_personal_message({'type': 'heartbeat_ack'}, client_id)
        elif message_type == 'subscribe':
            subscription = message.get('subscription')
            if subscription:
                success = await self.subscribe(client_id, subscription)
                await self.send_personal_message({
                    'type': 'subscription_response',
                    'subscription': subscription,
                    'success': success
                }, client_id)
        elif message_type == 'unsubscribe':
            subscription = message.get('subscription')
            if subscription:
                success = await self.unsubscribe(client_id, subscription)
                await self.send_personal_message({
                    'type': 'unsubscription_response',
                    'subscription': subscription,
                    'success': success
                }, client_id)
    
    async def _heartbeat_loop(self):
        while self.active_connections:
            try:
                await asyncio.sleep(30)
                current_time = datetime.now()
                dead_connections = []
                for client_id, connection in self.active_connections.items():
                    time_since_heartbeat = (current_time - connection.last_heartbeat).seconds
                    if time_since_heartbeat > 60:
                        dead_connections.append(client_id)
                    else:
                        try:
                            await connection.websocket.send_text(json.dumps({
                                'type': 'heartbeat_request',
                                'timestamp': current_time.isoformat()
                            }))
                        except Exception:
                            dead_connections.append(client_id)
                for client_id in dead_connections:
                    self.disconnect(client_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        total_connections = len(self.active_connections)
        subscriptions = {}
        for connection in self.active_connections.values():
            for sub in connection.subscriptions:
                subscriptions[sub] = subscriptions.get(sub, 0) + 1
        return {
            'total_connections': total_connections,
            'subscriptions': subscriptions,
            'active_clients': list(self.active_connections.keys())
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager() 