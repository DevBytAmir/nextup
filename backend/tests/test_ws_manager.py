from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

from backend.app.ws_manager import ConnectionManager


def _build_test_app() -> tuple[FastAPI, ConnectionManager]:
    app = FastAPI()
    manager = ConnectionManager()

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        await manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.post("/trigger")
    async def trigger(message: dict) -> dict:
        await manager.broadcast(message)
        return {"ok": True}

    return app, manager


def test_broadcast_reaches_all_connected_clients():
    app, _manager = _build_test_app()
    client = TestClient(app)

    with client.websocket_connect("/ws") as ws_a, client.websocket_connect("/ws") as ws_b:
        client.post("/trigger", json={"hello": "world"})

        assert ws_a.receive_json() == {"hello": "world"}
        assert ws_b.receive_json() == {"hello": "world"}


def test_broadcast_with_no_connections_does_not_raise():
    _app, manager = _build_test_app()

    import asyncio

    asyncio.run(manager.broadcast({"hello": "world"}))
