from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from .auth import check_pin, require_page
from .models import public_view
from .queue_logic import issue_number
from .store import save_state

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


async def _persist_and_broadcast(request: Request) -> None:
    save_state(request.app.state.data_path, request.app.state.queue_state)
    await request.app.state.manager.broadcast(public_view(request.app.state.queue_state))


@router.get("/state")
async def get_state(request: Request) -> dict:
    return public_view(request.app.state.queue_state)


@router.post("/number/issue", dependencies=[Depends(require_page("number"))])
async def issue(request: Request) -> dict:
    async with request.app.state.lock:
        ticket = issue_number(request.app.state.queue_state)
        await _persist_and_broadcast(request)
    return ticket.model_dump(mode="json")
