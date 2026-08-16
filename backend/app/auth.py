from __future__ import annotations

import secrets
from collections.abc import Callable

from fastapi import HTTPException, Request, status

from .models import Settings


def check_pin(page: str, pin: str, settings: Settings) -> bool:
    if page == "number":
        return secrets.compare_digest(pin, settings.numbering_pin)
    if page == "counter":
        return any(secrets.compare_digest(pin, p) for p in settings.counter_pins)
    if page == "admin":
        return secrets.compare_digest(pin, settings.admin_pin)
    return False


class SessionStore:
    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}

    def create(self, page: str) -> str:
        token = secrets.token_urlsafe(24)
        self._tokens[token] = page
        return token

    def page_for(self, token: str) -> str | None:
        return self._tokens.get(token)

    def is_valid(self, token: str, page: str) -> bool:
        return self._tokens.get(token) == page


def require_page(page: str) -> Callable:
    async def dependency(request: Request) -> None:
        header = request.headers.get("Authorization", "")
        token = header.removeprefix("Bearer ").strip()
        sessions: SessionStore = request.app.state.sessions
        if not token or not sessions.is_valid(token, page):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid or missing session",
            )

    return dependency
