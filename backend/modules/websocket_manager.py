#!/usr/bin/env python3
"""
WebSocket Manager for Site Builder
Handles WebSocket connections and broadcasts progress events during site generation.
Messages are scoped per job_id so clients only receive updates for their own jobs.
"""

from typing import Dict, Any, Optional
from fastapi import WebSocket
from datetime import datetime


class WebSocketManager:
    """
    Manages WebSocket connections scoped by job_id.
    Each client subscribes to a job_id and only receives messages for that job.
    Unsubscribed clients receive only connection_established.
    """

    def __init__(self):
        # All connected clients (for connection count)
        self.active_connections: list[WebSocket] = []
        # job_id -> list of subscribed WebSocket connections
        self.job_subscriptions: Dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

        print(
            f"[WS] Client connected | "
            f"Total connections: {len(self.active_connections)}"
        )

        await self._send(
            websocket,
            {
                "type": "connection_established",
                "timestamp": datetime.now().isoformat(),
                "message": "Connected to Site Builder Backend",
            },
        )

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection and all its subscriptions."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from all job subscriptions
        for job_id in list(self.job_subscriptions.keys()):
            if websocket in self.job_subscriptions[job_id]:
                self.job_subscriptions[job_id].remove(websocket)
            if not self.job_subscriptions[job_id]:
                del self.job_subscriptions[job_id]

        print(
            f"[WS] Client disconnected | "
            f"Total connections: {len(self.active_connections)}"
        )

    def subscribe(self, websocket: WebSocket, job_id: str):
        """Subscribe a client to receive updates for a specific job."""
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = []
        if websocket not in self.job_subscriptions[job_id]:
            self.job_subscriptions[job_id].append(websocket)
            print(f"[WS] Client subscribed to job {job_id}")

    async def _send(self, websocket: WebSocket, data: dict):
        """Send JSON data to a specific client."""
        try:
            await websocket.send_json(data)
        except Exception as e:
            print(f"[WS] Failed to send to client: {e}")
            self.disconnect(websocket)

    async def send_to_job(self, job_id: str, data: dict):
        """Send JSON data only to clients subscribed to this job_id."""
        subscribers = self.job_subscriptions.get(job_id, [])
        if not subscribers:
            return

        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat()

        disconnected: list[WebSocket] = []
        for ws in subscribers:
            try:
                await ws.send_json(data)
            except Exception as e:
                print(f"[WS] Failed to send to job subscriber: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws)

    # ========================================================================
    # Site Builder Progress Events (all scoped to job_id)
    # ========================================================================

    async def broadcast_step(
        self,
        step: str,
        status: str,
        message: str,
        data: Optional[dict] = None,
    ):
        """Broadcast a site generation step event to the job's subscribers."""
        job_id = (data or {}).get("job_id", "")

        payload: Dict[str, Any] = {
            "type": "step",
            "step": step,
            "status": status,
            "message": message,
        }
        if data is not None:
            payload["data"] = data

        print(f"[WS] Step: {step} -> {status}: {message} (job={job_id})")

        if job_id:
            await self.send_to_job(job_id, payload)
        else:
            # Fallback: send to all (shouldn't happen in normal flow)
            for ws in list(self.active_connections):
                await self._send(ws, payload)

    async def broadcast_progress(self, percent: int, message: str, job_id: str = ""):
        """Broadcast an overall progress percentage update."""
        payload = {
            "type": "progress",
            "percent": percent,
            "message": message,
        }
        if job_id:
            await self.send_to_job(job_id, payload)
        else:
            for ws in list(self.active_connections):
                await self._send(ws, payload)

    async def broadcast_site_ready(self, site_data: dict):
        """Broadcast the final event when site generation is complete."""
        job_id = site_data.get("job_id", "")
        print(f"[WS] Site ready (job={job_id})")
        payload = {
            "type": "site_ready",
            "site": site_data,
        }
        if job_id:
            await self.send_to_job(job_id, payload)
        else:
            for ws in list(self.active_connections):
                await self._send(ws, payload)

    async def broadcast_error(
        self, error_message: str, details: Optional[dict] = None, job_id: str = ""
    ):
        """Broadcast an error event to the job's subscribers."""
        print(f"[WS] Error: {error_message} (job={job_id})")
        payload = {
            "type": "error",
            "message": error_message,
            "details": details or {},
        }
        if job_id:
            await self.send_to_job(job_id, payload)
        else:
            for ws in list(self.active_connections):
                await self._send(ws, payload)


# Global WebSocket manager instance
ws_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    return ws_manager
