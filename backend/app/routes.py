from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from .auth import check_pin

router = APIRouter(prefix="/api")

_VALID_PAGES = ("number", "counter", "admin")


class LoginRequest(BaseModel):
    page: str
    pin: str


class LoginResponse(BaseModel):
    token: str


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request) -> LoginResponse:
    if payload.page not in _VALID_PAGES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unknown page")
    settings = request.app.state.queue_state.settings
    if not check_pin(payload.page, payload.pin, settings):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid pin")
    token = request.app.state.sessions.create(payload.page)
    return LoginResponse(token=token)
