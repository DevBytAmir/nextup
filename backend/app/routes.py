from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from .auth import check_pin, require_page
from .models import public_view
from .queue_logic import call_next, has_active_ticket, issue_number, mark_done
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


class CounterRequest(BaseModel):
    counter: int


@router.post("/counter/call-next", dependencies=[Depends(require_page("counter"))])
async def call_next_route(payload: CounterRequest, request: Request) -> dict:
    async with request.app.state.lock:
        state = request.app.state.queue_state
        if has_active_ticket(state, payload.counter):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="this counter already has an active ticket",
            )
        ticket = call_next(state, payload.counter)
        if ticket is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="no one waiting")
        await _persist_and_broadcast(request)
    return ticket.model_dump(mode="json")


@router.post("/counter/done", dependencies=[Depends(require_page("counter"))])
async def done_route(payload: CounterRequest, request: Request) -> dict:
    async with request.app.state.lock:
        ticket = mark_done(request.app.state.queue_state, payload.counter)
        if ticket is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="no active ticket for this counter"
            )
        await _persist_and_broadcast(request)
    return ticket.model_dump(mode="json")
