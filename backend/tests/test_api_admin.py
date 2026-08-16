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
        ("/api/admin/settings", {"counter1_pin": "5555"}),
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


def test_update_settings_changes_counter_pins(client):
    admin_token = _login(client, "admin", "9999")

    res = client.post(
        "/api/admin/settings",
        json={"counter1_pin": "5555"},
        headers=_auth_headers(admin_token),
    )
    assert res.status_code == 200

    login_res = client.post("/api/login", json={"page": "counter", "pin": "5555"})
    assert login_res.status_code == 200
