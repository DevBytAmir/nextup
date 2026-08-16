from backend.app.models import AppState, TicketStatus
from backend.app.queue_logic import call_next, issue_number, mark_done


def test_issue_number_creates_waiting_ticket_and_increments_counter():
    state = AppState()

    first = issue_number(state)
    second = issue_number(state)

    assert first.number == 1
    assert first.status == TicketStatus.WAITING
    assert first.order == 1
    assert second.number == 2
    assert state.next_number == 3
    assert state.tickets == [first, second]


def test_call_next_returns_none_when_queue_empty():
    state = AppState()
    assert call_next(state, counter=1) is None


def test_call_next_claims_lowest_order_waiting_ticket():
    state = AppState()
    issue_number(state)  # #1
    issue_number(state)  # #2

    ticket = call_next(state, counter=1)

    assert ticket.number == 1
    assert ticket.status == TicketStatus.CALLED
    assert ticket.counter == 1


def test_call_next_twice_never_double_claims_same_ticket():
    state = AppState()
    issue_number(state)
    issue_number(state)

    first = call_next(state, counter=1)
    second = call_next(state, counter=2)

    assert first.number != second.number
    assert {first.number, second.number} == {1, 2}


def test_call_next_refuses_when_counter_already_has_an_active_ticket():
    state = AppState()
    issue_number(state)
    issue_number(state)
    call_next(state, counter=1)

    assert call_next(state, counter=1) is None


def test_mark_done_transitions_called_ticket_to_served():
    state = AppState()
    issue_number(state)
    call_next(state, counter=1)

    done = mark_done(state, counter=1)

    assert done.number == 1
    assert done.status == TicketStatus.SERVED


def test_mark_done_returns_none_when_counter_has_no_active_ticket():
    state = AppState()
    assert mark_done(state, counter=1) is None
