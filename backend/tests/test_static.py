import pytest


@pytest.mark.parametrize("path", ["/number", "/counter", "/admin", "/tv"])
def test_page_route_serves_html(client, path):
    res = client.get(path)
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert '<div id="app">' in res.text


def test_number_page_has_issue_button(client):
    page = client.get("/number")
    assert "/frontend/number/number.js" in page.text

    script = client.get("/frontend/number/number.js")
    assert script.status_code == 200
    assert 'id="issue-btn"' in script.text


def test_counter_page_has_call_next_button(client):
    page = client.get("/counter")
    assert "/frontend/counter/counter.js" in page.text

    script = client.get("/frontend/counter/counter.js")
    assert script.status_code == 200
    assert 'id="call-next-btn"' in script.text
    assert "data-counter" in script.text


def test_admin_page_has_ticket_table(client):
    page = client.get("/admin")
    assert "/frontend/admin/admin.js" in page.text

    script = client.get("/frontend/admin/admin.js")
    assert script.status_code == 200
    assert 'id="ticket-table"' in script.text


def test_tv_page_has_counter_tiles(client):
    page = client.get("/tv")
    assert "/frontend/tv/tv.js" in page.text

    script = client.get("/frontend/tv/tv.js")
    assert script.status_code == 200
    assert "renderCounterTiles" in script.text
    assert "counter-tile" in script.text
