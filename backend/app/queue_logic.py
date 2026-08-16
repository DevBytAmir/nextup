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


def has_active_ticket(state: AppState, counter: int) -> bool:
    return any(t.status == TicketStatus.CALLED and t.counter == counter for t in state.tickets)


def call_next(state: AppState, counter: int) -> Ticket | None:
    if has_active_ticket(state, counter):
        return None
    waiting = [t for t in state.tickets if t.status == TicketStatus.WAITING]
    if not waiting:
        return None
    ticket = min(waiting, key=lambda t: t.order)
    ticket.status = TicketStatus.CALLED
    ticket.counter = counter
    return ticket


def mark_done(state: AppState, counter: int) -> Ticket | None:
    for ticket in state.tickets:
        if ticket.status == TicketStatus.CALLED and ticket.counter == counter:
            ticket.status = TicketStatus.SERVED
            return ticket
    return None


def _find(state: AppState, number: int) -> Ticket | None:
    return next((t for t in state.tickets if t.number == number), None)
