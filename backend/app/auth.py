from __future__ import annotations

import secrets
from collections.abc import Callable

from fastapi import HTTPException, Request, status

from .models import Settings


def check_pin(page: str, pin: str, settings: Settings) -> bool:
    if page == "number":
        return secrets.compare_digest(pin, settings.numbering_pin)
    if page == "admin":
        return secrets.compare_digest(pin, settings.admin_pin)
    return False


def check_counter_pin(counter: int, pin: str, settings: Settings) -> bool:
    """Whether `pin` is specifically counter `counter`'s own PIN (1-based)."""
    if counter < 1 or counter > len(settings.counter_pins):
        return False
    return secrets.compare_digest(pin, settings.counter_pins[counter - 1])


class SessionStore:
    def __init__(self) -> None:
        self._tokens: dict[str, tuple[str, int | None]] = {}

    def create(self, page: str, counter: int | None = None) -> str:
        token = secrets.token_urlsafe(24)
        self._tokens[token] = (page, counter)
        return token

    def page_for(self, token: str) -> str | None:
        entry = self._tokens.get(token)
        return entry[0] if entry else None

    def is_valid(self, token: str, page: str) -> bool:
        entry = self._tokens.get(token)
        return entry is not None and entry[0] == page

    def counter_for(self, token: str) -> int | None:
        entry = self._tokens.get(token)
        return entry[1] if entry else None

    def invalidate_counter(self, counter: int) -> None:
        """Drop every counter session bound to this counter number."""
        for token in [t for t, entry in self._tokens.items() if entry == ("counter", counter)]:
            del self._tokens[token]

    def revoke(self, token: str) -> None:
        self._tokens.pop(token, None)


def bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    return header.removeprefix("Bearer ").strip()


def require_page(page: str) -> Callable:
    async def dependency(request: Request) -> None:
        token = bearer_token(request)
        sessions: SessionStore = request.app.state.sessions
        if not token or not sessions.is_valid(token, page):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid or missing session",
            )

    return dependency


async def require_counter(request: Request) -> int:
    token = bearer_token(request)
    sessions: SessionStore = request.app.state.sessions
    counter = sessions.counter_for(token) if token else None
    if not token or counter is None or not sessions.is_valid(token, "counter"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing session",
        )
    return counter
