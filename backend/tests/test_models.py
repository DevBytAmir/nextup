from backend.app.models import AppState, Settings, Ticket, TicketStatus, public_view


def test_default_app_state_is_empty_with_numbering_starting_at_one():
    state = AppState()
    assert state.tickets == []
    assert state.next_number == 1
    assert isinstance(state.settings, Settings)


def test_default_settings_have_expected_pins():
    settings = Settings()
    assert settings.numbering_pin == "1111"
    assert settings.counter_pins == ["2222", "3333"]
    assert settings.admin_pin == "9999"


def test_ticket_defaults_to_waiting_with_no_counter():
    ticket = Ticket(number=1, order=1)
    assert ticket.status == TicketStatus.WAITING
    assert ticket.counter is None


def test_public_view_excludes_settings_and_pins():
    state = AppState(tickets=[Ticket(number=1, order=1)], next_number=2)
    view = public_view(state)
    assert view == {
        "tickets": [{"number": 1, "status": "waiting", "counter": None, "order": 1}],
        "next_number": 2,
        "counter_count": 2,
        "sound_mode": "off",
    }
    assert "settings" not in view
    serialized = str(view)
    assert "1111" not in serialized
    assert "9999" not in serialized
