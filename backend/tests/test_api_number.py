def _login(client, page, pin):
    res = client.post("/api/login", json={"page": page, "pin": pin})
    return res.json()["token"]


def test_get_state_requires_no_auth_and_starts_empty(client):
    res = client.get("/api/state")
    assert res.status_code == 200
    assert res.json() == {"tickets": [], "next_number": 1}


def test_issue_without_token_returns_401(client):
    res = client.post("/api/number/issue")
    assert res.status_code == 401


def test_issue_with_valid_token_creates_ticket_and_updates_state(client):
    token = _login(client, "number", "1111")

    res = client.post("/api/number/issue", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    ticket = res.json()
    assert ticket["number"] == 1
    assert ticket["status"] == "waiting"

    state = client.get("/api/state").json()
    assert state["next_number"] == 2
    assert state["tickets"][0]["number"] == 1


def test_issue_persists_to_disk(client, data_path):
    import json

    token = _login(client, "number", "1111")
    client.post("/api/number/issue", headers={"Authorization": f"Bearer {token}"})

    raw = json.loads(data_path.read_text(encoding="utf-8"))
    assert raw["next_number"] == 2
