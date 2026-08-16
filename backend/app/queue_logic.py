from __future__ import annotations

from .models import AppState, Ticket, TicketStatus


def issue_number(state: AppState) -> Ticket:
    ticket = Ticket(
        number=state.next_number,
        status=TicketStatus.WAITING,
        counter=None,
        order=state.next_number,
    )
    state.tickets.append(ticket)
    state.next_number += 1
    return ticket


def _find(state: AppState, number: int) -> Ticket | None:
    return next((t for t in state.tickets if t.number == number), None)
