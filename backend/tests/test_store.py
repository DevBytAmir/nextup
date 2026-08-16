import json

from backend.app.models import AppState, Ticket
from backend.app.store import default_state, load_state, save_state


def test_default_state_has_no_tickets_and_next_number_one():
    state = default_state()
    assert state.tickets == []
    assert state.next_number == 1


def test_load_state_creates_default_file_when_missing(tmp_path):
    path = tmp_path / "state.json"
    assert not path.exists()

    state = load_state(path)

    assert path.exists()
    assert state.tickets == []
    assert state.next_number == 1


def test_save_then_load_roundtrips_data(tmp_path):
    path = tmp_path / "nested" / "state.json"
    state = AppState(tickets=[Ticket(number=7, order=7)], next_number=8)

    save_state(path, state)
    loaded = load_state(path)

    assert loaded.next_number == 8
    assert loaded.tickets[0].number == 7


def test_save_state_writes_readable_json(tmp_path):
    path = tmp_path / "state.json"
    save_state(path, AppState(next_number=5))

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["next_number"] == 5
