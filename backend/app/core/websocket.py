from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: dict):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                print(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """WebSocket endpoint for real-time execution updates"""
    if not client_id:
        client_id = str(id(websocket))

    await manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Could handle ping/pong or client commands
            await manager.send_message(client_id, {"type": "pong", "data": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(client_id)

# Helper function to be used by executor to send updates
async def send_execution_update(execution_id: int, update: dict):
    """Send execution update to clients subscribed to this execution"""
    message = {
        "type": "execution_update",
        "execution_id": execution_id,
        "data": update
    }
    await manager.send_message(f"execution_{execution_id}", message)