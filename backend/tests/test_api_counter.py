import asyncio

import httpx


def _login(client, page, pin, counter=None):
    res = client.post("/api/login", json={"page": page, "pin": pin, "counter": counter})
    return res.json()["token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_binds_a_counter_session_to_the_matching_counter_number(client):
    res = client.post("/api/login", json={"page": "counter", "pin": "2222", "counter": 1})
    assert res.status_code == 200
    assert res.json()["counter"] == 1

    res = client.post("/api/login", json={"page": "counter", "pin": "3333", "counter": 2})
    assert res.status_code == 200
    assert res.json()["counter"] == 2


def test_whoami_reports_the_counter_bound_to_the_session(client):
    token = _login(client, "counter", "3333", counter=2)
    res = client.get("/api/counter/whoami", headers=_auth_headers(token))
    assert res.status_code == 200
    assert res.json() == {"counter": 2}


def test_whoami_without_token_returns_401(client):
    res = client.get("/api/counter/whoami")
    assert res.status_code == 401


def test_call_next_without_token_returns_401(client):
    res = client.post("/api/counter/call-next")
    assert res.status_code == 401


def test_call_next_with_empty_queue_returns_409(client):
    token = _login(client, "counter", "2222", counter=1)
    res = client.post("/api/counter/call-next", headers=_auth_headers(token))
    assert res.status_code == 409


def test_call_next_claims_and_done_serves(client):
    number_token = _login(client, "number", "1111")
    client.post("/api/number/issue", headers=_auth_headers(number_token))

    counter_token = _login(client, "counter", "2222", counter=1)
    called = client.post("/api/counter/call-next", headers=_auth_headers(counter_token))
    assert called.status_code == 200
    assert called.json()["status"] == "called"
    assert called.json()["counter"] == 1

    done = client.post("/api/counter/done", headers=_auth_headers(counter_token))
    assert done.status_code == 200
    assert done.json()["status"] == "served"


def test_a_counters_pin_cannot_be_used_to_act_as_another_counter(client):
    number_token = _login(client, "number", "1111")
    client.post("/api/number/issue", headers=_auth_headers(number_token))

    counter1_token = _login(client, "counter", "2222", counter=1)
    counter2_token = _login(client, "counter", "3333", counter=2)

    called = client.post("/api/counter/call-next", headers=_auth_headers(counter1_token))
    assert called.json()["counter"] == 1

    # counter 2's session can't claim the ticket counter 1 is already holding,
    # and calling next itself always operates as counter 2, never counter 1.
    res = client.post("/api/counter/call-next", headers=_auth_headers(counter2_token))
    assert res.status_code == 409
    assert res.json()["detail"] == "no one waiting"


def test_call_next_while_already_active_returns_distinct_409(client):
    number_token = _login(client, "number", "1111")
    client.post("/api/number/issue", headers=_auth_headers(number_token))
    client.post("/api/number/issue", headers=_auth_headers(number_token))

    counter_token = _login(client, "counter", "2222", counter=1)
    first = client.post("/api/counter/call-next", headers=_auth_headers(counter_token))
    assert first.status_code == 200

    second = client.post("/api/counter/call-next", headers=_auth_headers(counter_token))
    assert second.status_code == 409
    assert second.json()["detail"] == "this counter already has an active ticket"


def test_done_without_active_ticket_returns_404(client):
    token = _login(client, "counter", "2222", counter=1)
    res = client.post("/api/counter/done", headers=_auth_headers(token))
    assert res.status_code == 404


def test_recall_previous_without_token_returns_401(client):
    res = client.post("/api/counter/recall-previous")
    assert res.status_code == 401


def test_recall_previous_with_no_history_returns_404(client):
    token = _login(client, "counter", "2222", counter=1)
    res = client.post("/api/counter/recall-previous", headers=_auth_headers(token))
    assert res.status_code == 404


def test_recall_previous_undoes_a_misclicked_done(client):
    number_token = _login(client, "number", "1111")
    client.post("/api/number/issue", headers=_auth_headers(number_token))

    counter_token = _login(client, "counter", "2222", counter=1)
    client.post("/api/counter/call-next", headers=_auth_headers(counter_token))
    client.post("/api/counter/done", headers=_auth_headers(counter_token))

    res = client.post("/api/counter/recall-previous", headers=_auth_headers(counter_token))
    assert res.status_code == 200
    body = res.json()
    assert body["number"] == 1
    assert body["status"] == "called"
    assert body["counter"] == 1


async def test_simultaneous_call_next_from_both_counters_never_double_claims(app):
    from backend.app.auth import SessionStore

    app.state.sessions = SessionStore()
    number_token = app.state.sessions.create("number")
    counter1_token = app.state.sessions.create("counter", 1)
    counter2_token = app.state.sessions.create("counter", 2)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/api/number/issue", headers=_auth_headers(number_token))

        results = await asyncio.gather(
            ac.post("/api/counter/call-next", headers=_auth_headers(counter1_token)),
            ac.post("/api/counter/call-next", headers=_auth_headers(counter2_token)),
        )

    statuses = sorted(r.status_code for r in results)
    assert statuses == [200, 409]
