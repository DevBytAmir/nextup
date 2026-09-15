def test_health_check_returns_ok(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_ws_sends_public_view_on_connect(client):
    with client.websocket_connect("/ws") as ws:
        message = ws.receive_json()
    assert message == {
        "tickets": [],
        "next_number": 1,
        "counter_count": 2,
        "sound_mode": "off",
    }


def test_ws_disconnect_always_removes_the_connection(client, app):
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        assert len(app.state.manager._connections) == 1

    assert len(app.state.manager._connections) == 0


def test_app_loads_existing_state_from_disk(data_path, app):
    from backend.app.main import create_app
    from backend.app.models import AppState, Ticket
    from backend.app.store import save_state

    save_state(data_path, AppState(tickets=[Ticket(number=5, order=5)], next_number=6))

    reloaded = create_app(data_path)
    assert reloaded.state.queue_state.next_number == 6
