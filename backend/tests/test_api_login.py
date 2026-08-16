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


def test_login_accepts_either_counter_pin(client):
    res1 = client.post("/api/login", json={"page": "counter", "pin": "2222"})
    res2 = client.post("/api/login", json={"page": "counter", "pin": "3333"})
    assert res1.status_code == 200
    assert res2.status_code == 200
