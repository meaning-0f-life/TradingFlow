from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

class ConnectionManager:
    """Manages WebSocket connections for real-time updates with subscription support"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        # Track which executions each client is subscribed to
        # Format: {client_id: Set[execution_id]}
        self.subscriptions: Dict[str, Set[int]] = {}
        # Track which clients are subscribed to each execution
        # Format: {execution_id: Set[client_id]}
        self.execution_subscribers: Dict[int, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()
        print(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        # Remove from all subscriptions
        if client_id in self.subscriptions:
            subscribed_executions = self.subscriptions[client_id]
            for execution_id in subscribed_executions:
                if execution_id in self.execution_subscribers:
                    self.execution_subscribers[execution_id].discard(client_id)
                    # Clean up empty execution subscription sets
                    if not self.execution_subscribers[execution_id]:
                        del self.execution_subscribers[execution_id]
            del self.subscriptions[client_id]
        
        # Remove connection
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        print(f"Client {client_id} disconnected")

    async def handle_message(self, client_id: str, message: dict):
        """Handle incoming messages from client (subscribe/unsubscribe)"""
        try:
            message_type = message.get('type')
            execution_id = message.get('execution_id')
            
            if not execution_id or not isinstance(execution_id, int):
                return
            
            if message_type == 'subscribe':
                await self.subscribe_to_execution(client_id, execution_id)
            elif message_type == 'unsubscribe':
                await self.unsubscribe_from_execution(client_id, execution_id)
        except Exception as e:
            print(f"Error handling message from {client_id}: {e}")

    async def subscribe_to_execution(self, client_id: str, execution_id: int):
        """Subscribe a client to updates for a specific execution"""
        if client_id not in self.subscriptions:
            self.subscriptions[client_id] = set()
        
        self.subscriptions[client_id].add(execution_id)
        
        if execution_id not in self.execution_subscribers:
            self.execution_subscribers[execution_id] = set()
        
        self.execution_subscribers[execution_id].add(client_id)
        print(f"Client {client_id} subscribed to execution {execution_id}")

    async def unsubscribe_from_execution(self, client_id: str, execution_id: int):
        """Unsubscribe a client from updates for a specific execution"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(execution_id)
        
        if execution_id in self.execution_subscribers:
            self.execution_subscribers[execution_id].discard(client_id)
            if not self.execution_subscribers[execution_id]:
                del self.execution_subscribers[execution_id]
        
        print(f"Client {client_id} unsubscribed from execution {execution_id}")

    async def send_to_subscribers(self, execution_id: int, message: dict):
        """Send message to all clients subscribed to a specific execution"""
        if execution_id not in self.execution_subscribers:
            return
        
        # Get a copy of subscribers to avoid modification during iteration
        subscribers = list(self.execution_subscribers[execution_id])
        disconnected = []
        
        for client_id in subscribers:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    print(f"Error sending to {client_id}: {e}")
                    disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
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
            # Receive messages from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await manager.handle_message(client_id, message)
            except json.JSONDecodeError:
                print(f"Invalid JSON received from {client_id}")
            except Exception as e:
                print(f"Error processing message from {client_id}: {e}")
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(client_id)

# Helper function to be used by executor to send updates
async def send_execution_update(execution_id: int, update: dict):
    """Send execution update to all clients subscribed to this execution"""
    message = {
        "type": "execution_update",
        "execution_id": execution_id,
        "data": update
    }
    await manager.send_to_subscribers(execution_id, message)
