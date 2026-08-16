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
