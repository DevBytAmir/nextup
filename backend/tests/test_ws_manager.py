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


def test_broadcast_prunes_a_connection_that_fails_to_send():
    import asyncio

    class _FailingSocket:
        async def send_text(self, _text: str) -> None:
            raise RuntimeError("boom")

    from backend.app.ws_manager import ConnectionManager

    manager = ConnectionManager()
    manager._connections.add(_FailingSocket())

    asyncio.run(manager.broadcast({"hello": "world"}))

    assert len(manager._connections) == 0


def test_broadcast_reaches_every_client_even_if_one_disconnects_mid_send():
    import asyncio

    from backend.app.ws_manager import ConnectionManager

    manager = ConnectionManager()
    received: list[dict] = []

    class _SlowThenDisconnectingSocket:
        async def send_text(self, text: str) -> None:
            # simulate this connection dropping out from under a concurrent
            # broadcast before its own send would have completed
            manager.disconnect(self)
            raise RuntimeError("dropped")

    class _NormalSocket:
        async def send_text(self, text: str) -> None:
            received.append(text)

    dropping = _SlowThenDisconnectingSocket()
    normal = _NormalSocket()
    manager._connections.add(dropping)
    manager._connections.add(normal)

    asyncio.run(manager.broadcast({"hello": "world"}))

    assert len(received) == 1
    assert dropping not in manager._connections
