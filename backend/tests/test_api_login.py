def test_login_with_correct_pin_returns_token(client):
    res = client.post("/api/login", json={"page": "admin", "pin": "9999"})
    assert res.status_code == 200
    assert "token" in res.json()


def test_login_with_wrong_pin_returns_401(client):
    res = client.post("/api/login", json={"page": "admin", "pin": "0000"})
    assert res.status_code == 401


def test_login_with_unknown_page_returns_400(client):
    res = client.post("/api/login", json={"page": "tv", "pin": "0000"})
    assert res.status_code == 400


def test_login_accepts_a_counter_pin_for_its_own_counter(client):
    res1 = client.post("/api/login", json={"page": "counter", "pin": "2222", "counter": 1})
    res2 = client.post("/api/login", json={"page": "counter", "pin": "3333", "counter": 2})
    assert res1.status_code == 200
    assert res1.json()["counter"] == 1
    assert res2.status_code == 200
    assert res2.json()["counter"] == 2


def test_login_rejects_a_counter_pin_used_for_a_different_counter(client):
    res = client.post("/api/login", json={"page": "counter", "pin": "3333", "counter": 1})
    assert res.status_code == 401


def test_login_for_counter_page_without_counter_returns_400(client):
    res = client.post("/api/login", json={"page": "counter", "pin": "2222"})
    assert res.status_code == 400


def test_logout_revokes_the_token(client):
    login_res = client.post("/api/login", json={"page": "admin", "pin": "9999"})
    token = login_res.json()["token"]

    logout_res = client.post("/api/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200

    res = client.post(
        "/api/admin/skip", json={"number": 1}, headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 401


def test_logout_without_a_token_does_not_error(client):
    res = client.post("/api/logout")
    assert res.status_code == 200
