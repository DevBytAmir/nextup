from __future__ import annotations

import asyncio
import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        if not self._connections:
            return
        payload = json.dumps(message)
        targets = list(self._connections)
        results = await asyncio.gather(
            *(connection.send_text(payload) for connection in targets),
            return_exceptions=True,
        )
        for connection, result in zip(targets, results, strict=True):
            if isinstance(result, Exception):
                self.disconnect(connection)
