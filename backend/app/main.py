from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auth import SessionStore
from .models import public_view
from .routes import router
from .store import load_state
from .ws_manager import ConnectionManager

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_PATH = BASE_DIR / "data" / "state.json"
FRONTEND_DIR = BASE_DIR / "frontend"


def create_app(data_path: Path) -> FastAPI:
    app = FastAPI(title="NextUp")
    app.state.data_path = data_path
    app.state.queue_state = load_state(data_path)
    app.state.lock = asyncio.Lock()
    app.state.manager = ConnectionManager()
    app.state.sessions = SessionStore()
    app.include_router(router)

    @app.middleware("http")
    async def no_cache(request: Request, call_next):
        response = await call_next(request)
        if not request.url.path.startswith("/frontend/"):
            response.headers["Cache-Control"] = "no-cache"
        return response

    @app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        manager: ConnectionManager = websocket.app.state.manager
        await manager.connect(websocket)
        await websocket.send_json(public_view(websocket.app.state.queue_state))
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

    for page in ("number", "counter", "admin", "tv"):

        def make_page_handler(page_name: str):
            async def handler() -> FileResponse:
                return FileResponse(FRONTEND_DIR / page_name / "index.html")

            return handler

        app.add_api_route(f"/{page}", make_page_handler(page), methods=["GET"])

    return app


app = create_app(DEFAULT_DATA_PATH)
