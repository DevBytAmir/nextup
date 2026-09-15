from backend.app.models import AppState, TicketStatus
from backend.app.queue_logic import (
    call_next,
    delete_ticket,
    issue_number,
    issue_numbers,
    mark_done,
    recall_previous,
    reorder_ticket,
    requeue_ticket,
    skip_ticket,
)


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


def test_issue_numbers_creates_the_requested_count_in_sequence():
    state = AppState()
    issue_number(state)  # #1, so bulk issuing continues from #2

    tickets = issue_numbers(state, 3)

    assert [t.number for t in tickets] == [2, 3, 4]
    assert all(t.status == TicketStatus.WAITING for t in tickets)
    assert state.next_number == 5


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
    issue_number(state)  # #1
    issue_number(state)  # #2
    call_next(state, counter=1)

    assert call_next(state, counter=1) is None
    still_waiting = [t for t in state.tickets if t.status == TicketStatus.WAITING]
    assert [t.number for t in still_waiting] == [2]


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


def test_skip_ticket_moves_waiting_ticket_to_skipped():
    state = AppState()
    issue_number(state)

    skipped = skip_ticket(state, number=1)

    assert skipped.status == TicketStatus.SKIPPED


def test_skip_ticket_frees_the_counter_to_call_the_next_waiting_ticket():
    state = AppState()
    issue_number(state)  # #1
    issue_number(state)  # #2
    call_next(state, counter=1)

    skipped = skip_ticket(state, number=1)
    assert skipped.status == TicketStatus.SKIPPED

    next_ticket = call_next(state, counter=1)
    assert next_ticket.number == 2


def test_skip_ticket_preserves_which_counter_skipped_it():
    state = AppState()
    issue_number(state)
    call_next(state, counter=1)

    skipped = skip_ticket(state, number=1)

    assert skipped.counter == 1


def test_skip_ticket_returns_none_for_already_served_ticket():
    state = AppState()
    issue_number(state)
    call_next(state, counter=1)
    mark_done(state, counter=1)

    assert skip_ticket(state, number=1) is None


def test_skip_ticket_returns_none_for_unknown_number():
    state = AppState()
    assert skip_ticket(state, number=999) is None


def test_requeue_ticket_moves_skipped_ticket_to_back_of_waiting_order():
    state = AppState()
    issue_number(state)  # #1
    issue_number(state)  # #2
    skip_ticket(state, number=1)

    requeued = requeue_ticket(state, number=1)

    assert requeued.status == TicketStatus.WAITING
    assert requeued.order > next(t for t in state.tickets if t.number == 2).order


def test_requeue_ticket_order_never_collides_with_a_later_issued_ticket():
    state = AppState()
    issue_number(state)  # #1
    issue_number(state)  # #2
    skip_ticket(state, number=1)
    requeue_ticket(state, number=1)

    later = issue_number(state)  # #3, issued after the requeue

    ordered = sorted(state.tickets, key=lambda t: t.order)
    assert [t.number for t in ordered] == [2, 1, 3]
    assert later.order != next(t for t in state.tickets if t.number == 1).order


def test_requeue_ticket_returns_none_for_already_waiting_ticket():
    state = AppState()
    issue_number(state)
    assert requeue_ticket(state, number=1) is None


def test_requeue_ticket_moves_served_ticket_back_to_waiting():
    state = AppState()
    issue_number(state)
    call_next(state, counter=1)
    mark_done(state, counter=1)

    requeued = requeue_ticket(state, number=1)

    assert requeued.status == TicketStatus.WAITING
    assert requeued.counter is None


def test_requeue_ticket_moves_called_ticket_back_to_waiting():
    state = AppState()
    issue_number(state)
    call_next(state, counter=1)

    requeued = requeue_ticket(state, number=1)

    assert requeued.status == TicketStatus.WAITING
    assert requeued.counter is None


def test_requeue_ticket_returns_none_for_unknown_number():
    state = AppState()
    assert requeue_ticket(state, number=999) is None


def test_recall_previous_returns_none_when_counter_has_no_history():
    state = AppState()
    assert recall_previous(state, counter=1) is None


def test_recall_previous_returns_none_while_counter_has_active_ticket():
    state = AppState()
    issue_number(state)
    call_next(state, counter=1)

    assert recall_previous(state, counter=1) is None


def test_recall_previous_recalls_most_recently_served_ticket_for_that_counter():
    state = AppState()
    issue_number(state)  # #1
    issue_number(state)  # #2
    call_next(state, counter=1)
    mark_done(state, counter=1)
    call_next(state, counter=1)
    mark_done(state, counter=1)

    recalled = recall_previous(state, counter=1)

    assert recalled.number == 2
    assert recalled.status == TicketStatus.CALLED
    assert recalled.counter == 1


def test_recall_previous_uses_actual_recency_not_ticket_number():
    state = AppState()
    issue_number(state)  # #1
    issue_number(state)  # #2
    call_next(state, counter=1)  # claims #1
    mark_done(state, counter=1)  # #1 served
    requeue_ticket(state, number=1)  # #1 back to waiting, now behind #2
    call_next(state, counter=1)  # claims #2
    mark_done(state, counter=1)  # #2 served
    call_next(state, counter=1)  # claims #1 again (the true most recent)
    mark_done(state, counter=1)  # #1 served again, more recently than #2

    recalled = recall_previous(state, counter=1)

    assert recalled.number == 1


def test_recall_previous_recalls_a_skipped_ticket_too():
    state = AppState()
    issue_number(state)
    call_next(state, counter=1)
    skip_ticket(state, number=1)

    recalled = recall_previous(state, counter=1)

    assert recalled.number == 1
    assert recalled.status == TicketStatus.CALLED


def test_recall_previous_ignores_tickets_touched_by_a_different_counter():
    state = AppState()
    issue_number(state)
    call_next(state, counter=1)
    mark_done(state, counter=1)

    assert recall_previous(state, counter=2) is None


def test_delete_ticket_removes_ticket_regardless_of_status():
    state = AppState()
    issue_number(state)

    assert delete_ticket(state, number=1) is True
    assert state.tickets == []


def test_delete_ticket_returns_false_for_unknown_number():
    state = AppState()
    assert delete_ticket(state, number=1) is False


def test_reorder_ticket_up_swaps_order_with_previous_waiting_ticket():
    state = AppState()
    issue_number(state)  # #1
    issue_number(state)  # #2

    assert reorder_ticket(state, number=2, direction="up") is True

    ordered = sorted(state.tickets, key=lambda t: t.order)
    assert [t.number for t in ordered] == [2, 1]


def test_reorder_ticket_up_at_top_returns_false():
    state = AppState()
    issue_number(state)
    assert reorder_ticket(state, number=1, direction="up") is False


def test_reorder_ticket_down_at_bottom_returns_false():
    state = AppState()
    issue_number(state)
    assert reorder_ticket(state, number=1, direction="down") is False


def test_reorder_ticket_rejects_unknown_direction():
    state = AppState()
    issue_number(state)
    issue_number(state)
    assert reorder_ticket(state, number=1, direction="sideways") is False
