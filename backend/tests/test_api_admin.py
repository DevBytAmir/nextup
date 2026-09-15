def _login(client, page, pin):
    res = client.post("/api/login", json={"page": page, "pin": pin})
    return res.json()["token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _issue_ticket(client):
    token = _login(client, "number", "1111")
    client.post("/api/number/issue", headers=_auth_headers(token))


def test_admin_routes_require_admin_token(client):
    for path, body in [
        ("/api/admin/skip", {"number": 1}),
        ("/api/admin/requeue", {"number": 1}),
        ("/api/admin/delete", {"number": 1}),
        ("/api/admin/reorder", {"number": 1, "direction": "up"}),
        ("/api/admin/counters", {"counter_pins": ["5555"]}),
        ("/api/admin/sound-mode", {"sound_mode": "beep"}),
    ]:
        res = client.post(path, json=body)
        assert res.status_code == 401, path


def test_skip_then_requeue_ticket(client):
    _issue_ticket(client)
    admin_token = _login(client, "admin", "9999")

    skip_res = client.post(
        "/api/admin/skip", json={"number": 1}, headers=_auth_headers(admin_token)
    )
    assert skip_res.status_code == 200
    assert skip_res.json()["status"] == "skipped"

    requeue_res = client.post(
        "/api/admin/requeue", json={"number": 1}, headers=_auth_headers(admin_token)
    )
    assert requeue_res.status_code == 200
    assert requeue_res.json()["status"] == "waiting"


def test_skip_unknown_ticket_returns_404(client):
    admin_token = _login(client, "admin", "9999")
    res = client.post("/api/admin/skip", json={"number": 999}, headers=_auth_headers(admin_token))
    assert res.status_code == 404


def test_delete_ticket(client):
    _issue_ticket(client)
    admin_token = _login(client, "admin", "9999")

    res = client.post("/api/admin/delete", json={"number": 1}, headers=_auth_headers(admin_token))
    assert res.status_code == 200
    assert res.json() == {"deleted": True}

    state = client.get("/api/state").json()
    assert state["tickets"] == []


def test_delete_unknown_ticket_returns_404(client):
    admin_token = _login(client, "admin", "9999")
    res = client.post("/api/admin/delete", json={"number": 999}, headers=_auth_headers(admin_token))
    assert res.status_code == 404


def test_reorder_ticket(client):
    _issue_ticket(client)
    _issue_ticket(client)
    admin_token = _login(client, "admin", "9999")

    res = client.post(
        "/api/admin/reorder",
        json={"number": 2, "direction": "up"},
        headers=_auth_headers(admin_token),
    )
    assert res.status_code == 200
    assert res.json() == {"reordered": True}

    state = client.get("/api/state").json()
    ordered = sorted(state["tickets"], key=lambda t: t["order"])
    assert [t["number"] for t in ordered] == [2, 1]


def test_reorder_invalid_move_returns_404(client):
    _issue_ticket(client)
    admin_token = _login(client, "admin", "9999")

    res = client.post(
        "/api/admin/reorder",
        json={"number": 1, "direction": "up"},
        headers=_auth_headers(admin_token),
    )
    assert res.status_code == 404


def test_update_counters_changes_pins_and_count(client):
    admin_token = _login(client, "admin", "9999")

    res = client.post(
        "/api/admin/counters",
        json={"counter_pins": ["5555", "6666", "7777"]},
        headers=_auth_headers(admin_token),
    )
    assert res.status_code == 200
    assert res.json() == {"counter_count": 3}

    login_res = client.post("/api/login", json={"page": "counter", "pin": "5555"})
    assert login_res.status_code == 200

    state = client.get("/api/state").json()
    assert state["counter_count"] == 3


def test_update_counters_rejects_empty_list(client):
    admin_token = _login(client, "admin", "9999")
    res = client.post(
        "/api/admin/counters", json={"counter_pins": []}, headers=_auth_headers(admin_token)
    )
    assert res.status_code == 400


def test_update_counters_blank_pin_keeps_existing_pin(client):
    admin_token = _login(client, "admin", "9999")
    res = client.post(
        "/api/admin/counters",
        json={"counter_pins": ["1234", "  "]},
        headers=_auth_headers(admin_token),
    )
    assert res.status_code == 200

    changed_login = client.post("/api/login", json={"page": "counter", "pin": "1234"})
    assert changed_login.status_code == 200

    unchanged_login = client.post("/api/login", json={"page": "counter", "pin": "3333"})
    assert unchanged_login.status_code == 200


def test_update_counters_rejects_blank_pin_for_new_counter(client):
    admin_token = _login(client, "admin", "9999")
    res = client.post(
        "/api/admin/counters",
        json={"counter_pins": ["2222", "3333", ""]},
        headers=_auth_headers(admin_token),
    )
    assert res.status_code == 400


def test_update_counters_blocks_shrink_below_active_counter(client):
    _issue_ticket(client)
    counter_token = _login(client, "counter", "3333")
    call_res = client.post(
        "/api/counter/call-next", json={"counter": 2}, headers=_auth_headers(counter_token)
    )
    assert call_res.status_code == 200

    admin_token = _login(client, "admin", "9999")
    res = client.post(
        "/api/admin/counters",
        json={"counter_pins": ["5555"]},
        headers=_auth_headers(admin_token),
    )
    assert res.status_code == 409


def test_update_sound_mode_changes_public_state(client):
    admin_token = _login(client, "admin", "9999")

    state = client.get("/api/state").json()
    assert state["sound_mode"] == "off"

    res = client.post(
        "/api/admin/sound-mode",
        json={"sound_mode": "beep"},
        headers=_auth_headers(admin_token),
    )
    assert res.status_code == 200
    assert res.json() == {"sound_mode": "beep"}

    state = client.get("/api/state").json()
    assert state["sound_mode"] == "beep"


def test_update_sound_mode_rejects_unknown_value(client):
    admin_token = _login(client, "admin", "9999")
    res = client.post(
        "/api/admin/sound-mode",
        json={"sound_mode": "loud"},
        headers=_auth_headers(admin_token),
    )
    assert res.status_code == 422


def test_requeue_ticket_from_served_status(client):
    _issue_ticket(client)
    counter_token = _login(client, "counter", "2222")
    client.post("/api/counter/call-next", json={"counter": 1}, headers=_auth_headers(counter_token))
    client.post("/api/counter/done", json={"counter": 1}, headers=_auth_headers(counter_token))

    admin_token = _login(client, "admin", "9999")
    res = client.post("/api/admin/requeue", json={"number": 1}, headers=_auth_headers(admin_token))
    assert res.status_code == 200
    assert res.json()["status"] == "waiting"
