from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """
    Manages active WebSocket connections for ticket rooms.
    Allows connecting, disconnecting, and broadcasting messages to clients.
    """
    def __init__(self) -> None:
        """
        Initialize the connection manager.
        Creates an empty dictionary for active connections.
        """
        self.active: Dict[int, List[WebSocket]] = {}

    async def connect(self, ticket_id: int, ws: WebSocket):
        """
        Accept and register a new WebSocket connection for a ticket room.

        Args:
            ticket_id: The ticket room ID.
            ws: The WebSocket connection to add.
        """
        await ws.accept()
        self.active.setdefault(ticket_id, []).append(ws)

    def disconnect(self, ticket_id: int, ws: WebSocket):
        """
        Remove a WebSocket connection from a ticket room.

        Args:
            ticket_id: The ticket room ID.
            ws: The WebSocket connection to remove.
        """
        connections = self.active.get(ticket_id, [])
        if ws in connections:
            connections.remove(ws)

    async def broadcast(self, ticket_id: int, message: str):
        """
        Send a message to all WebSocket clients in a ticket room.

        Args:
            ticket_id: The ticket room ID.
            message: The message to broadcast.
        """
        for ws in self.active.get(ticket_id, []):
            await ws.send_text(message)


manager = ConnectionManager()
