#!/usr/bin/env python3
"""
WebSocket Manager for Site Builder
Handles WebSocket connections and broadcasts progress events during site generation.
Adapted from the orchestrator WebSocket manager pattern.
"""

from typing import List, Dict, Any, Optional
from fastapi import WebSocket
from datetime import datetime


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts site generation progress
    events to all connected clients.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """
        Accept a new WebSocket connection and register it.

        Args:
            websocket: The WebSocket connection to accept.
            client_id: Optional identifier for the client.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

        client_id = client_id or f"client_{len(self.active_connections)}"
        print(
            f"[WS] Client connected: {client_id} | "
            f"Total connections: {len(self.active_connections)}"
        )

        await self.send_to_client(
            websocket,
            {
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "message": "Connected to Site Builder Backend",
            },
        )

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection from the active list.

        Args:
            websocket: The WebSocket connection to remove.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(
                f"[WS] Client disconnected | "
                f"Total connections: {len(self.active_connections)}"
            )

    async def send_to_client(self, websocket: WebSocket, data: dict):
        """
        Send JSON data to a specific client.

        Args:
            websocket: The target WebSocket connection.
            data: Dictionary payload to send as JSON.
        """
        try:
            await websocket.send_json(data)
        except Exception as e:
            print(f"[WS] Failed to send to client: {e}")
            self.disconnect(websocket)

    async def broadcast(self, data: dict):
        """
        Send JSON data to all connected clients.
        Automatically adds a timestamp and cleans up dead connections.

        Args:
            data: Dictionary payload to broadcast as JSON.
        """
        if not self.active_connections:
            return

        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat()

        disconnected: List[WebSocket] = []

        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                print(f"[WS] Failed to broadcast to client: {e}")
                disconnected.append(connection)

        # Clean up dead connections
        for ws in disconnected:
            self.disconnect(ws)

    # ========================================================================
    # Site Builder Progress Events
    # ========================================================================

    async def broadcast_step(
        self,
        step: str,
        status: str,
        message: str,
        data: Optional[dict] = None,
    ):
        """
        Broadcast a site generation step event.

        Args:
            step: The current step identifier. One of:
                  "parsing_url", "scraping_profile", "extracting_photos",
                  "generating_content", "rendering_template"
            status: The step status. One of:
                    "started", "progress", "completed", "error"
            message: Human-readable description of what is happening.
            data: Optional extra data relevant to this step.
        """
        payload: Dict[str, Any] = {
            "type": "step",
            "step": step,
            "status": status,
            "message": message,
        }
        if data is not None:
            payload["data"] = data

        print(f"[WS] Step: {step} -> {status}: {message}")
        await self.broadcast(payload)

    async def broadcast_progress(self, percent: int, message: str):
        """
        Broadcast an overall progress percentage update.

        Args:
            percent: Progress percentage (0-100).
            message: Human-readable progress description.
        """
        await self.broadcast(
            {
                "type": "progress",
                "percent": percent,
                "message": message,
            }
        )

    async def broadcast_site_ready(self, site_data: dict):
        """
        Broadcast the final event when site generation is complete.

        Args:
            site_data: Dictionary containing the generated site information
                       (e.g., URL, preview HTML, metadata).
        """
        print(f"[WS] Site ready")
        await self.broadcast(
            {
                "type": "site_ready",
                "site": site_data,
            }
        )

    async def broadcast_error(
        self, error_message: str, details: Optional[dict] = None
    ):
        """
        Broadcast an error event to all clients.

        Args:
            error_message: Human-readable error description.
            details: Optional dictionary with additional error context.
        """
        print(f"[WS] Error: {error_message}")
        await self.broadcast(
            {
                "type": "error",
                "message": error_message,
                "details": details or {},
            }
        )


# Global WebSocket manager instance
ws_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    return ws_manager
