"""WebSocket connection manager for real-time frontend streaming."""
import json
import logging
from typing import List, Set
from fastapi import WebSocket, WebSocketDisconnect
from backend.shared.models import EventMessage

logger = logging.getLogger("ew.gateway.ws")


class ConnectionManager:
    """Manages active WebSocket connections from frontend clients."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected to WebSocket. Total active clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove disconnected WebSocket client."""
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Remaining active clients: {len(self.active_connections)}")

    async def broadcast_event(self, event_message: EventMessage) -> None:
        """Broadcast an EventMessage to all connected WebSocket clients."""
        if not self.active_connections:
            return

        payload_json = json.dumps(event_message.model_dump(), default=str)
        disconnected_clients: List[WebSocket] = []

        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload_json)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}. Marking for disconnection.")
                disconnected_clients.append(connection)

        for client in disconnected_clients:
            self.disconnect(client)

    async def broadcast_raw(self, message_dict: dict) -> None:
        """Broadcast a raw dictionary as JSON."""
        if not self.active_connections:
            return

        payload_json = json.dumps(message_dict, default=str)
        disconnected_clients: List[WebSocket] = []

        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload_json)
            except Exception as e:
                logger.warning(f"Failed to send raw message to client: {e}")
                disconnected_clients.append(connection)

        for client in disconnected_clients:
            self.disconnect(client)


ws_manager = ConnectionManager()
