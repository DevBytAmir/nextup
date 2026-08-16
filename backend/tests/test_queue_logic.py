from backend.app.models import AppState, TicketStatus
from backend.app.queue_logic import issue_number


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
