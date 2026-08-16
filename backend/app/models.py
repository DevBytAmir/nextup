from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class TicketStatus(StrEnum):
    WAITING = "waiting"
    CALLED = "called"
    SERVED = "served"
    SKIPPED = "skipped"


class Ticket(BaseModel):
    number: int
    status: TicketStatus = TicketStatus.WAITING
    counter: int | None = None
    order: int


class Settings(BaseModel):
    numbering_pin: str = "1111"
    counter_pins: list[str] = Field(default_factory=lambda: ["2222", "3333"])
    admin_pin: str = "9999"


class AppState(BaseModel):
    tickets: list[Ticket] = Field(default_factory=list)
    next_number: int = 1
    settings: Settings = Field(default_factory=Settings)


def public_view(state: AppState) -> dict:
    """State as sent to clients: tickets + numbering only, never PINs."""
    return {
        "tickets": [t.model_dump(mode="json") for t in state.tickets],
        "next_number": state.next_number,
        "counter_count": len(state.settings.counter_pins),
    }
