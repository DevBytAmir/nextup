from __future__ import annotations

from .models import AppState, Ticket, TicketStatus


def issue_number(state: AppState) -> Ticket:
    ticket = Ticket(
        number=state.next_number,
        status=TicketStatus.WAITING,
        counter=None,
        order=state.next_order,
    )
    state.tickets.append(ticket)
    state.next_number += 1
    state.next_order += 1
    return ticket


def issue_numbers(state: AppState, count: int) -> list[Ticket]:
    return [issue_number(state) for _ in range(count)]


def _touch(state: AppState, ticket: Ticket) -> None:
    """Stamp a ticket with the current action sequence, for true recency."""
    ticket.touched_at = state.next_sequence
    state.next_sequence += 1


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
    _touch(state, ticket)
    return ticket


def mark_done(state: AppState, counter: int) -> Ticket | None:
    for ticket in state.tickets:
        if ticket.status == TicketStatus.CALLED and ticket.counter == counter:
            ticket.status = TicketStatus.SERVED
            _touch(state, ticket)
            return ticket
    return None


def skip_ticket(state: AppState, number: int) -> Ticket | None:
    """Set a ticket aside. The counter field is kept (not cleared) so a
    later recall_previous can still find which counter skipped it."""
    ticket = _find(state, number)
    if ticket is None or ticket.status not in (TicketStatus.WAITING, TicketStatus.CALLED):
        return None
    ticket.status = TicketStatus.SKIPPED
    _touch(state, ticket)
    return ticket


def requeue_ticket(state: AppState, number: int) -> Ticket | None:
    """Send a ticket back to the waiting line, from any status but waiting itself."""
    ticket = _find(state, number)
    if ticket is None or ticket.status == TicketStatus.WAITING:
        return None
    ticket.status = TicketStatus.WAITING
    ticket.counter = None
    ticket.order = state.next_order
    state.next_order += 1
    _touch(state, ticket)
    return ticket


def recall_previous(state: AppState, counter: int) -> Ticket | None:
    """Undo this counter's most recent served/skipped ticket, e.g. after a misclick."""
    if has_active_ticket(state, counter):
        return None
    candidates = [
        t
        for t in state.tickets
        if t.counter == counter and t.status in (TicketStatus.SERVED, TicketStatus.SKIPPED)
    ]
    if not candidates:
        return None
    ticket = max(candidates, key=lambda t: t.touched_at)
    ticket.status = TicketStatus.CALLED
    _touch(state, ticket)
    return ticket


def delete_ticket(state: AppState, number: int) -> bool:
    ticket = _find(state, number)
    if ticket is None:
        return False
    state.tickets.remove(ticket)
    return True


def reorder_ticket(state: AppState, number: int, direction: str) -> bool:
    if direction not in ("up", "down"):
        return False
    waiting = sorted(
        (t for t in state.tickets if t.status == TicketStatus.WAITING),
        key=lambda t: t.order,
    )
    idx = next((i for i, t in enumerate(waiting) if t.number == number), None)
    if idx is None:
        return False
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if swap_idx < 0 or swap_idx >= len(waiting):
        return False
    waiting[idx].order, waiting[swap_idx].order = waiting[swap_idx].order, waiting[idx].order
    return True


def _find(state: AppState, number: int) -> Ticket | None:
    return next((t for t in state.tickets if t.number == number), None)
