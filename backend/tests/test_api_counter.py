import asyncio

import httpx


def _login(client, page, pin):
    res = client.post("/api/login", json={"page": page, "pin": pin})
    return res.json()["token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_call_next_without_token_returns_401(client):
    res = client.post("/api/counter/call-next", json={"counter": 1})
    assert res.status_code == 401


def test_call_next_with_empty_queue_returns_409(client):
    token = _login(client, "counter", "2222")
    res = client.post("/api/counter/call-next", json={"counter": 1}, headers=_auth_headers(token))
    assert res.status_code == 409


def test_call_next_claims_and_done_serves(client):
    number_token = _login(client, "number", "1111")
    client.post("/api/number/issue", headers=_auth_headers(number_token))

    counter_token = _login(client, "counter", "2222")
    called = client.post(
        "/api/counter/call-next", json={"counter": 1}, headers=_auth_headers(counter_token)
    )
    assert called.status_code == 200
    assert called.json()["status"] == "called"

    done = client.post(
        "/api/counter/done", json={"counter": 1}, headers=_auth_headers(counter_token)
    )
    assert done.status_code == 200
    assert done.json()["status"] == "served"


def test_call_next_while_already_active_returns_distinct_409(client):
    number_token = _login(client, "number", "1111")
    client.post("/api/number/issue", headers=_auth_headers(number_token))
    client.post("/api/number/issue", headers=_auth_headers(number_token))

    counter_token = _login(client, "counter", "2222")
    first = client.post(
        "/api/counter/call-next", json={"counter": 1}, headers=_auth_headers(counter_token)
    )
    assert first.status_code == 200

    second = client.post(
        "/api/counter/call-next", json={"counter": 1}, headers=_auth_headers(counter_token)
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "this counter already has an active ticket"


def test_done_without_active_ticket_returns_404(client):
    token = _login(client, "counter", "2222")
    res = client.post("/api/counter/done", json={"counter": 1}, headers=_auth_headers(token))
    assert res.status_code == 404


def test_recall_previous_without_token_returns_401(client):
    res = client.post("/api/counter/recall-previous", json={"counter": 1})
    assert res.status_code == 401


def test_recall_previous_with_no_history_returns_404(client):
    token = _login(client, "counter", "2222")
    res = client.post(
        "/api/counter/recall-previous", json={"counter": 1}, headers=_auth_headers(token)
    )
    assert res.status_code == 404


def test_recall_previous_undoes_a_misclicked_done(client):
    number_token = _login(client, "number", "1111")
    client.post("/api/number/issue", headers=_auth_headers(number_token))

    counter_token = _login(client, "counter", "2222")
    client.post("/api/counter/call-next", json={"counter": 1}, headers=_auth_headers(counter_token))
    client.post("/api/counter/done", json={"counter": 1}, headers=_auth_headers(counter_token))

    res = client.post(
        "/api/counter/recall-previous", json={"counter": 1}, headers=_auth_headers(counter_token)
    )
    assert res.status_code == 200
    assert res.json() == {"number": 1, "status": "called", "counter": 1, "order": 1}


async def test_simultaneous_call_next_from_both_counters_never_double_claims(app):
    from backend.app.auth import SessionStore

    app.state.sessions = SessionStore()
    number_token = app.state.sessions.create("number")
    counter_token = app.state.sessions.create("counter")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/api/number/issue", headers=_auth_headers(number_token))

        results = await asyncio.gather(
            ac.post(
                "/api/counter/call-next", json={"counter": 1}, headers=_auth_headers(counter_token)
            ),
            ac.post(
                "/api/counter/call-next", json={"counter": 2}, headers=_auth_headers(counter_token)
            ),
        )

    statuses = sorted(r.status_code for r in results)
    assert statuses == [200, 409]
