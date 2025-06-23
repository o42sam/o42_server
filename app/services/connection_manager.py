

import json
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):

        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """Accepts a new WebSocket connection and maps it to a user."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, user_id: str):
        """Removes a user's WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message_data: dict, user_id: str):
        """Sends a JSON message to a specific user if they are connected."""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message_data)
            print(f"Sent message to user {user_id}")
        else:
            print(f"User {user_id} is not online. Message will be stored.")


manager = ConnectionManager()