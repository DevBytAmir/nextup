from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from .auth import check_pin, require_page
from .models import SoundMode, TicketStatus, public_view
from .queue_logic import (
    call_next,
    delete_ticket,
    has_active_ticket,
    issue_number,
    issue_numbers,
    mark_done,
    recall_previous,
    reorder_ticket,
    requeue_ticket,
    skip_ticket,
)
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


class TicketNumberRequest(BaseModel):
    number: int


class ReorderRequest(BaseModel):
    number: int
    direction: str


class CounterPinsRequest(BaseModel):
    counter_pins: list[str]


@router.post("/admin/skip", dependencies=[Depends(require_page("admin"))])
async def skip_route(payload: TicketNumberRequest, request: Request) -> dict:
    async with request.app.state.lock:
        ticket = skip_ticket(request.app.state.queue_state, payload.number)
        if ticket is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="cannot skip ticket")
        await _persist_and_broadcast(request)
    return ticket.model_dump(mode="json")


@router.post("/admin/requeue", dependencies=[Depends(require_page("admin"))])
async def requeue_route(payload: TicketNumberRequest, request: Request) -> dict:
    async with request.app.state.lock:
        ticket = requeue_ticket(request.app.state.queue_state, payload.number)
        if ticket is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="cannot requeue ticket"
            )
        await _persist_and_broadcast(request)
    return ticket.model_dump(mode="json")


@router.post("/admin/delete", dependencies=[Depends(require_page("admin"))])
async def delete_route(payload: TicketNumberRequest, request: Request) -> dict:
    async with request.app.state.lock:
        deleted = delete_ticket(request.app.state.queue_state, payload.number)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ticket not found")
        await _persist_and_broadcast(request)
    return {"deleted": True}


@router.post("/admin/reorder", dependencies=[Depends(require_page("admin"))])
async def reorder_route(payload: ReorderRequest, request: Request) -> dict:
    async with request.app.state.lock:
        moved = reorder_ticket(request.app.state.queue_state, payload.number, payload.direction)
        if not moved:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="cannot reorder ticket"
            )
        await _persist_and_broadcast(request)
    return {"reordered": True}


class BulkIssueRequest(BaseModel):
    count: int = Field(ge=1, le=200)


@router.post("/admin/issue-bulk", dependencies=[Depends(require_page("admin"))])
async def issue_bulk_route(payload: BulkIssueRequest, request: Request) -> dict:
    async with request.app.state.lock:
        tickets = issue_numbers(request.app.state.queue_state, payload.count)
        await _persist_and_broadcast(request)
    return {"tickets": [t.model_dump(mode="json") for t in tickets]}


@router.post("/admin/counters", dependencies=[Depends(require_page("admin"))])
async def update_counters(payload: CounterPinsRequest, request: Request) -> dict:
    pins = [p.strip() for p in payload.counter_pins]
    if not pins:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="need at least one counter",
        )
    async with request.app.state.lock:
        state = request.app.state.queue_state
        existing_pins = state.settings.counter_pins
        # blank entry = keep the current PIN for that counter
        resolved_pins = [
            pin or (existing_pins[i] if i < len(existing_pins) else "")
            for i, pin in enumerate(pins)
        ]
        if any(not p for p in resolved_pins):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="new counters need a PIN",
            )
        new_count = len(resolved_pins)
        active_out_of_range = any(
            t.status == TicketStatus.CALLED and t.counter is not None and t.counter > new_count
            for t in state.tickets
        )
        if active_out_of_range:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="finish or skip active tickets on the counters being removed first",
            )
        state.settings.counter_pins = resolved_pins
        await _persist_and_broadcast(request)
    return {"counter_count": new_count}


class SoundModeRequest(BaseModel):
    sound_mode: SoundMode


@router.post("/admin/sound-mode", dependencies=[Depends(require_page("admin"))])
async def update_sound_mode(payload: SoundModeRequest, request: Request) -> dict:
    async with request.app.state.lock:
        state = request.app.state.queue_state
        state.settings.sound_mode = payload.sound_mode
        await _persist_and_broadcast(request)
    return {"sound_mode": payload.sound_mode.value}


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


@router.post("/counter/recall-previous", dependencies=[Depends(require_page("counter"))])
async def recall_previous_route(payload: CounterRequest, request: Request) -> dict:
    async with request.app.state.lock:
        ticket = recall_previous(request.app.state.queue_state, payload.counter)
        if ticket is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="nothing to recall")
        await _persist_and_broadcast(request)
    return ticket.model_dump(mode="json")
